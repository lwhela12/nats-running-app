Nat's Running App – MVP Design Document
1. Purpose

The app helps users set realistic running goals, generate a personalized training plan, and adapt the plan based on ongoing feedback. It is aimed at recreational to intermediate runners who want structured guidance without hiring a coach.

2. Scope (MVP)

In-scope features:

Chat-based onboarding (distance, time, age, sex, current fitness).

Goal feasibility check with trade-off negotiation.

Training plan generator (algorithmic, periodized).

Calendar with scheduled workouts.

Logging runs (completion, time, distance, perceived effort).

Adaptation rules (simple adjustments for fatigue or missed sessions).

User authentication and persistence.

Out of scope (for MVP):

AI-driven personalization.

Integration with wearables (Garmin, Strava, Apple Health).

Social/sharing features.

Nutrition/injury modules.

3. User Flows
3.1 Onboarding

User signs up/logs in.

Chat-style Q&A:

Comfortable distance & time.

Age & sex.

Goal distance (+ optional target time).

Target date.

Feasibility engine checks if goal is realistic.

If feasible → generate plan.

If not feasible → present trade-offs (“Which would you compromise: distance, time, or date?”).

3.2 Plan View

Calendar shows workouts (color-coded by type: easy, long, intervals, rest).

User can tap on a day to see workout details.

3.3 Logging

User marks workout as complete.

Inputs: actual distance, time, perceived effort (easy/medium/hard).

Optional notes.

3.4 Adaptation

If 3+ “hard” easy runs logged → reduce next week’s volume by 10%.

If 2+ missed key workouts in 10 days → insert recovery week.

If progress is ahead of schedule → modest pace/volume increase.

4. Core Algorithms
4.1 Projection

Use Riegel formula to estimate target time feasibility:

𝑇
2
=
𝑇
1
×
(
𝐷
2
/
𝐷
1
)
1.06
T
2
	​

=T
1
	​

×(D
2
	​

/D
1
	​

)
1.06

Weekly volume increases capped at 5–10%.

4.2 Plan Generation

Phases: Base → Build → Peak → Taper.

Weekly structure: 3–5 days running, rest/cross-training included.

Workouts: easy runs, long runs, tempos, intervals.

Cut-back weeks every 3–4 weeks.

4.3 Adaptation Rules

Rule-based (if/else), no AI for MVP.

Adjusts volume, intensity, or inserts recovery weeks.

5. Architecture
5.1 Frontend

Tech: React (Next.js).

Features:

Chat-style onboarding UI.

Calendar (FullCalendar or similar).

Run logging form.

Progress dashboard.

5.2 Backend

Tech: FastAPI (Python) or Flask (if you prefer).

Features:

Auth (JWT or OAuth).

Feasibility engine.

Plan generator service.

Adaptation service.

Workout CRUD APIs.

5.3 Database (Postgres)

User(id, email, age, sex)

Goal(id, user_id, distance, target_time, target_date)

Plan(id, user_id, goal_id, start_date, end_date)

Workout(id, plan_id, date, type, target_distance, target_pace, notes)

SessionLog(id, workout_id, actual_distance, actual_time, rpe, notes)

AdaptationEvent(id, plan_id, date, rule_applied, before_state, after_state)

6. Non-Functional Requirements

Performance: Plan generation < 2 seconds.

Scalability: Single DB instance sufficient for MVP; modular backend for later expansion.

Security: JWT-based auth, encrypted passwords.

Reliability: Daily adaptation job runs via cron/queue worker.

Usability: Simple, friendly chatbot-style onboarding; clear workout instructions.

7. Risks & Mitigations

Risk: Users set unsafe goals.

Mitigation: Hard caps on weekly increases, mandatory trade-off negotiation.

Risk: Drop-off after onboarding.

Mitigation: Clear progress feedback, simple run logging, lightweight nudges.

Risk: Injury from overtraining.

Mitigation: Rule-based safety rails, enforced recovery weeks.

8. Future Enhancements

AI-driven coaching (natural language chat, personalized adjustments).

Wearable/app integrations (Strava, Garmin, Apple Health).

Social accountability features (friend plans, leaderboards).

Premium subscription tier (advanced analytics, custom coaching).