# Agents.md — Running Plan App MVP

This document instructs a coding agent on how to implement the MVP running-plan application using a deterministic, algorithmic core (no AI at runtime). Follow the steps, conventions, and acceptance criteria below.

---

## 0) Mission & Guardrails
**Mission:** Ship a production-ready MVP that: (1) onboards a runner via chat UI, (2) evaluates goal feasibility, (3) generates a periodized training plan, (4) schedules workouts on a calendar, (5) lets users log sessions with RPE and times, and (6) auto-adapts plans with simple rules.

**Non-goals (MVP):** Wearable integrations, social features, AI coaching, nutrition/injury modules.

**Hard safety rails:** Weekly volume cap (max +10% WoW), mandatory cut-back week every 3–4 weeks, never schedule 2 intensity days back-to-back, adapt down on sustained high RPE.

**Performance:** Plan generation < 2 seconds for typical plans (< 32 weeks). All API endpoints p95 < 300 ms under light load.

**Security:** JWT auth, salted password hashing (argon2 preferred), input validation, role: user only.

---

## 1) Tech Stack & Project Layout

### 1.1 Stack
- **Frontend:** Next.js (App Router), TypeScript, TailwindCSS, FullCalendar for calendar UI, React Hook Form + Zod for validation.
- **Backend:** FastAPI (Python 3.11+), Uvicorn/Gunicorn, Pydantic v2, SQLAlchemy 2.x.
- **DB:** Postgres 15+.
- **Workers:** RQ (Redis-backed) for nightly adaptation jobs and on-demand recompute.
- **Auth:** JWT (access + refresh), httpOnly cookies.
- **Infra:** Vercel (frontend), Railway or Fly.io (API + Postgres + Redis). CI via GitHub Actions.

### 1.2 Repo Layout (monorepo)
```
/                     
  /apps
    /web              # Next.js app
    /api              # FastAPI service
  /packages
    /schemas          # Shared OpenAPI types & TS models (generated)
    /ui               # Shared UI components
    /config           # ESLint, Prettier, Tailwind config
  /ops
    /docker           # Dockerfiles, compose for local dev
    /migrations       # Alembic migrations
    /ci               # GitHub Actions workflows
```

---

## 2) Data Model (Postgres)

### 2.1 Tables
```sql
-- users
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  age INT NOT NULL CHECK (age BETWEEN 13 AND 95),
  sex TEXT NOT NULL CHECK (sex IN ('male','female','other')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- goals
CREATE TABLE goals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  distance_m INT NOT NULL CHECK (distance_m BETWEEN 1000 AND 100000),
  target_time_sec INT, -- nullable (distance-only goal)
  target_date DATE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- capability_snapshots (user-reported current fitness)
CREATE TABLE capability_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  comfortable_distance_m INT NOT NULL,
  comfortable_time_sec INT NOT NULL,
  projection JSONB NOT NULL, -- store derived paces, predicted times
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- plans
CREATE TABLE plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  goal_id UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('active','archived','superseded')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- workouts (scheduled)
CREATE TABLE workouts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id UUID NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
  wdate DATE NOT NULL,
  wtype TEXT NOT NULL CHECK (wtype IN ('easy','long','tempo','interval','rest','cross')),
  target_distance_m INT,     -- prefer distance OR duration
  target_duration_sec INT,
  target_zone TEXT,          -- easy, aerobic, threshold, vo2, etc.
  description TEXT,
  is_key BOOLEAN NOT NULL DEFAULT false
);

-- session_logs (actuals)
CREATE TABLE session_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workout_id UUID NOT NULL REFERENCES workouts(id) ON DELETE CASCADE,
  actual_distance_m INT,
  actual_time_sec INT,
  rpe INT CHECK (rpe BETWEEN 1 AND 10),
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- adaptation_events (audit)
CREATE TABLE adaptation_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id UUID NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
  event_date DATE NOT NULL,
  rule TEXT NOT NULL,
  before_state JSONB NOT NULL,
  after_state JSONB NOT NULL
);
```

### 2.2 Indexes & Constraints
- Foreign keys as above.
- Index on `workouts(plan_id, wdate)`.
- Only one `plans.status='active'` per `goal_id` (enforce with partial unique index or app logic).

---

## 3) Domain Algorithms

### 3.1 Projection (Riegel)
```
T2 = T1 * (D2/D1)^1.06
```
- Default exponent `k=1.06` (configurable 1.02–1.10). Store in `projection` JSON: predicted 5K, 10K, HM, M times; derive pace zones.

### 3.2 Pace Zones (derived from current fitness)
- easy: 60–75% HRmax or ~ +60–120 s/mi slower than 10K pace
- aerobic steady: ~ +30–60 s/mi vs 10K pace
- threshold: ~10–20 s/mi slower than 10K pace (20–40 min continuous or cruise intervals)
- intervals/VO₂: 3–5 min reps faster than 5K pace, equal/shorter recovery
- long: easy–steady; allow last 15–25% at steady/goal pace later in cycle

### 3.3 Feasibility & Trade-offs
- Inputs: today, target_date, current weekly volume (derived from capability; if unknown, infer from comfortable run: `weekly_volume_start ≈ 2.5–3.5 × comfortable_distance`).
- Caps: weekly volume growth ≤ 10%; quality sessions ≤ 2/week; long run ≤ 30–35% of weekly volume.
- Check if reaching (distance, optional target_time) within available weeks is possible.
- If not feasible, calculate minimum relaxation needed for each lever:
  1) **Push date**: weeks_needed – weeks_available.
  2) **Relax time**: adjust target pace until progression fits caps.
  3) **Reduce distance**: smallest distance meeting caps by target date.
- Return a ranked recommendation.

### 3.4 Plan Generation
- Split total weeks into phases: Base (40–55%), Build (25–35%), Peak (10–20%), Taper (10–15%).
- Insert a cut-back week every 3–4 weeks (–15–25% volume).
- Weekly templates by running days (3–5), e.g.,
  - 3 days: Easy / Rest / Easy / Rest / Long / Rest / Cross
  - 5 days: Easy / Quality / Easy / Rest / Quality-light / Long / Rest
- Populate workouts with distance/duration and target zone; mark long + quality as `is_key=true`.

### 3.5 Adaptation Rules (nightly job and on log submit)
- **High fatigue:** if 3 consecutive easy/steady runs logged with RPE ≥ 7 → reduce next week volume by 10% and remove 1 quality session.
- **Missed key workouts:** if ≥2 missed key sessions in last 10 days → insert 7-day recovery microcycle (all easy, –20% volume).
- **Ahead of schedule:** if 14-day trend shows easy runs completed ≥10 s/mi faster than assigned with RPE ≤ 4 → +5% volume cap next block; small pace bump.
- **Bounds:** never change more than one lever per week; keep changes ≤10% volume, ≤10 s/mi pace.

---

## 4) API Design (FastAPI)

### 4.1 Auth
- `POST /auth/register` {email, password, age, sex}
- `POST /auth/login` {email, password}
- `POST /auth/refresh`

### 4.2 Onboarding & Capability
- `POST /capability` {comfortable_distance_m, comfortable_time_sec, date}
- `GET /capability/latest`

### 4.3 Goals & Plans
- `POST /goals` {distance_m, target_time_sec?, target_date}
- `POST /goals/{id}/feasibility` → {feasible: bool, reasons[], tradeoffs[]}
- `POST /goals/{id}/generate-plan` → creates plan + workouts
- `GET /plans/current` → active plan with workouts

### 4.4 Workouts & Logging
- `GET /plans/{plan_id}/workouts?from=YYYY-MM-DD&to=YYYY-MM-DD`
- `POST /workouts/{id}/log` {actual_distance_m?, actual_time_sec?, rpe, notes?}
- `GET /workouts/{id}`

### 4.5 Adaptation & Insights
- `POST /plans/{id}/recompute` (admin/worker)
- `GET /plans/{id}/adaptation-events`

### 4.6 OpenAPI & Codegen
- Export OpenAPI JSON; generate TS types into `/packages/schemas` (use `openapi-typescript`).

---

## 5) Frontend UX Specs (Next.js)

### 5.1 Onboarding (chat UI)
- Steps:
  1. "If you went for a run right now, what distance would be comfortable?"
  2. "About how long would it take?"
  3. Age & sex.
  4. Goal distance (+ optional finish time), target date (picker).
- After answers, call `/goals/.../feasibility`; show meter (green/amber/red) + trade-off picker. Persist on confirm → generate plan.

### 5.2 Calendar
- FullCalendar month/week view. Colors: easy (green), long (blue), quality (orange), rest (gray).
- Click workout → drawer with details, pace guidance, and a "Log run" button.

### 5.3 Logging Form
- Inputs: distance, time, RPE (1–10), notes. Post to `/workouts/{id}/log`. After success, show banner if adaptation triggered.

### 5.4 Insights
- Simple cards: adherence %, last 7 days RPE trend, next key workout.

---

## 6) Core Modules & Function Signatures (API)

```python
# apps/api/domain/projection.py
@dataclass
class FitnessProjection:
    distance_m: int
    predicted_time_sec: int

DEFAULT_RIEGEL_K = 1.06

def riegel_predict(t1_sec: int, d1_m: int, d2_m: int, k: float = DEFAULT_RIEGEL_K) -> int:
    """Return predicted time (sec) for distance d2 given t1@d1."""

# apps/api/domain/zones.py
def derive_zones(predicted_10k_sec: int) -> dict:
    """Return pace windows per zone in sec/km and sec/mi."""

# apps/api/domain/feasibility.py
@dataclass
class FeasibilityResult:
    feasible: bool
    reasons: list[str]
    tradeoffs: list[dict]  # {lever: 'date'|'time'|'distance', recommendation: ...}

def assess_feasibility(goal, capability, weeks_available: int) -> FeasibilityResult:
    ...

# apps/api/domain/planner.py
@dataclass
class PlanSpec:
    start_date: date
    end_date: date
    running_days_per_week: int
    phases: dict

@dataclass
class WorkoutSpec:
    wdate: date
    wtype: str
    target_distance_m: int | None
    target_duration_sec: int | None
    target_zone: str | None
    description: str
    is_key: bool

def generate_plan(goal, capability, plan_spec: PlanSpec) -> list[WorkoutSpec]:
    ...

# apps/api/domain/adaptation.py
def evaluate_and_apply_adaptations(plan_id: UUID, as_of: date) -> list[dict]:
    """Applies rules; returns adaptation events created."""
```

---

## 7) Validation, Testing, and Quality

### 7.1 Validation
- Use Pydantic schemas on the API. Zod on the frontend. Reject impossible combinations (e.g., 2 km in 5 minutes for a novice unless clearly stated).

### 7.2 Unit Tests (pytest)
- `riegel_predict` (monotonicity, exponent variants, boundary distances)
- `assess_feasibility` with scenarios: feasible, must push date, must relax time, must reduce distance
- `generate_plan` invariants: cut-back weeks inserted, long run ≤ 35% volume, no back-to-back intensity
- `evaluate_and_apply_adaptations` scenarios for each rule path

### 7.3 Integration Tests
- Full onboarding → plan generation → logging → adaptation loop with a fixed seed.

### 7.4 Linters & Formatters
- Python: ruff + black. Type-check with mypy.
- TS: eslint + prettier + tsc strict.

### 7.5 Git Hygiene
- Conventional Commits (`feat:`, `fix:`, `refactor:`).
- PR template includes: scope, screenshots, tests, risks.

---

## 8) Config & Environment

**Backend `.env`**
```
DATABASE_URL=postgresql+psycopg://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
JWT_SECRET=...
ACCESS_TOKEN_TTL=900
REFRESH_TOKEN_TTL=1209600
ALLOWED_ORIGINS=https://app.example.com,http://localhost:3000
RIEGEL_K=1.06
WEEKLY_VOLUME_CAP=0.10
```

**Frontend `.env.local`**
```
NEXT_PUBLIC_API_BASE=https://api.example.com
```

**Migrations:** Use Alembic with autogenerate; store in `/ops/migrations`.

---

## 9) CI/CD
- **CI:**
  - Install deps, run linters, run tests, build web.
  - Generate OpenAPI and check for breaking schema changes (oapi-diff).
- **CD:**
  - On `main` push: deploy API to Railway, web to Vercel. Run Alembic migrate. Smoke test `/healthz`.

---

## 10) Observability
- API request logging (structured JSON), error tracking (Sentry), metrics (Prometheus if available), health endpoint `/healthz`.
- App analytics: pageviews, funnel for onboarding completion, adherence %.

---

## 11) Runbooks

### 11.1 Recompute Plan
- Trigger `POST /plans/{id}/recompute` or enqueue `recompute_plan(plan_id)` in RQ.

### 11.2 Adaptation Job (Nightly)
- Cron: `0 2 * * *` (API timezone). Fetch active plans; call `evaluate_and_apply_adaptations`.

### 11.3 Hotfix Bad Plan
- Set current plan `status='superseded'`; regenerate from latest capability & goal; migrate unfinished workouts forward by weekday.

---

## 12) Acceptance Criteria (MVP)
- User can complete onboarding in < 2 minutes.
- Feasibility endpoint returns deterministic output for fixed inputs.
- Generated plans comply with caps and include taper.
- Calendar renders all workouts for the active plan.
- Logging a session updates adherence stats and can trigger adaptations; events are persisted.
- All invariants covered by tests; >90% statement coverage in domain modules.

---

## 13) Seed Data & Fixtures
- Create seed user with a 10K goal 14 weeks out, comfortable 3 mi in 30:00. Generate plan and 2 weeks of synthetic logs with random RPE ~N(5,1).

---

## 14) Future Hooks (post-MVP)
- Health/wearable import layer (Strava/Garmin/Apple Health).
- LLM onboarding parser (text → normalized capability & goals).
- Personalization model (tiny tabular model on RPE/time trends).

---

## 15) Task Graph (First 2 Sprints)

**Sprint 1 (Backend-first)**
1. Scaffold FastAPI, auth, base schemas.
2. Implement `riegel_predict`, zones, feasibility.
3. Alembic migrations for core tables.
4. Plan generator + invariants.
5. Workouts CRUD + list by date range.
6. OpenAPI export + schemas package.

**Sprint 2 (Frontend + Adaptation)**
1. Next.js app scaffold, auth screens.
2. Chat-style onboarding flow; call feasibility + generate plan.
3. Calendar view with workout drawer.
4. Logging form + API integration.
5. Adaptation rules + nightly job.
6. Insights cards + adherence metric.

---

## 16) UX Copy (MVP)
- Feasibility red: "We can absolutely get you there, but not on this timeline. Which is easier to adjust: date, finish time, or distance?"
- Adaptation fatigue: "Your last few runs felt tougher than expected. I’ve lightened next week to help you absorb the work."

---

## 17) Definition of Done
- All acceptance criteria met.
- CI green; deploys succeed; health checks pass.
- Owner walkthrough: create user → onboarding → plan → log → see adaptation.
- Draft privacy policy & disclaimer present.

