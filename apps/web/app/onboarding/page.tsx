"use client";
import { useEffect, useMemo, useState } from "react";
import { ChatMessage } from "@/components/Chat";
import { apiCapabilityCreate, apiFeasibility, apiGeneratePlan, apiGoalCreate } from "@/lib/api";
import { format, addWeeks } from "date-fns";

type Step =
  | { key: "welcome" }
  | { key: "cap_distance" }
  | { key: "cap_time"; distance_m: number }
  | { key: "goal"; distance_m: number; time_sec: number }
  | { key: "feasibility"; goalId: string; goal: { distance_m: number; target_time_sec?: number | null; target_date: string } }
  | { key: "done" };

function toMeters(value: number, unit: "mi" | "km") { return Math.round(value * (unit === "mi" ? 1609.34 : 1000)); }
function timeToSec(min: number, sec: number) { return Math.round(min * 60 + sec); }

export default function OnboardingPage() {
  const [steps, setSteps] = useState<Step[]>([{ key: "welcome" }]);
  const [unit, setUnit] = useState<"mi" | "km">("mi");
  const cur = steps[steps.length - 1];

  // UI controls state
  const [distanceVal, setDistanceVal] = useState<number>(3);
  const [capMin, setCapMin] = useState<number>(30);
  const [capSec, setCapSec] = useState<number>(0);
  const [goalDistance, setGoalDistance] = useState<number>(10000);
  const [goalHasTime, setGoalHasTime] = useState(false);
  const [goalMin, setGoalMin] = useState<number>(50);
  const [goalSec, setGoalSec] = useState<number>(0);
  const [goalDate, setGoalDate] = useState<string>(() => format(addWeeks(new Date(), 16), "yyyy-MM-dd"));
  const [feas, setFeas] = useState<{ feasible: boolean; reasons: string[]; tradeoffs: Array<{ lever: string; recommendation: any }>; } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const access = localStorage.getItem("nra_access");
    if (!access) window.location.href = "/login";
  }, []);

  async function submitCapability() {
    setLoading(true); setError(null);
    try {
      const comfortable_distance_m = toMeters(distanceVal, unit);
      const comfortable_time_sec = timeToSec(capMin, capSec);
      await apiCapabilityCreate({ date: format(new Date(), "yyyy-MM-dd"), comfortable_distance_m, comfortable_time_sec });
      setSteps((s) => [...s, { key: "goal", distance_m: comfortable_distance_m, time_sec: comfortable_time_sec }]);
    } catch (e: any) { setError(e.message); } finally { setLoading(false); }
  }

  async function checkFeas(goal: { distance_m: number; target_time_sec?: number | null; target_date: string }) {
    setLoading(true); setError(null);
    try {
      const g = await apiGoalCreate(goal);
      const res = await apiFeasibility(g.id);
      setFeas(res);
      setSteps((s) => [...s, { key: "feasibility", goalId: g.id, goal }]);
    } catch (e: any) { setError(e.message); } finally { setLoading(false); }
  }

  async function generate(goalId: string) {
    setLoading(true); setError(null);
    try { await apiGeneratePlan(goalId); window.location.href = "/calendar"; } catch (e: any) { setError(e.message); } finally { setLoading(false); }
  }

  function applyTradeoffApply(t: { lever: string; recommendation: any }) {
    if (cur.key !== "feasibility") return;
    let g = { ...cur.goal };
    if (t.lever === "date" && t.recommendation?.push_weeks) {
      const d = new Date(g.target_date);
      d.setDate(d.getDate() + 7 * Number(t.recommendation.push_weeks));
      g.target_date = format(d, "yyyy-MM-dd");
    }
    if (t.lever === "time" && t.recommendation?.relax_seconds) {
      const tt = (g.target_time_sec ?? 0) + Number(t.recommendation.relax_seconds);
      g.target_time_sec = Math.max(0, tt);
    }
    if (t.lever === "distance" && t.recommendation?.suggest_distance_m) {
      g.distance_m = Number(t.recommendation.suggest_distance_m);
    }
    // reset and re-check
    setFeas(null);
    setSteps((s) => s.slice(0, s.length - 1));
    void checkFeas(g);
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Onboarding</h1>
      <div className="bg-white border rounded p-4">
        <ChatMessage role="system">If you went for a run right now, what distance would be comfortable?</ChatMessage>
        {cur.key === "welcome" || cur.key === "cap_distance" ? (
          <div className="mt-2 flex items-center gap-2">
            <input type="number" min={0.5} step={0.5} className="w-24 border rounded p-2" value={distanceVal} onChange={(e)=>setDistanceVal(Number(e.target.value))} />
            <select className="border rounded p-2" value={unit} onChange={(e)=>setUnit(e.target.value as any)}>
              <option value="mi">mi</option>
              <option value="km">km</option>
            </select>
            <button className="ml-2 bg-black text-white px-3 py-2 rounded" onClick={()=>setSteps([{ key: "cap_time", distance_m: toMeters(distanceVal, unit) }])}>Next</button>
          </div>
        ) : null}

        {cur.key === "cap_time" && (
          <div className="mt-4 space-y-2">
            <ChatMessage role="system">About how long would it take?</ChatMessage>
            <div className="flex gap-2 items-center">
              <input type="number" min={0} className="w-24 border rounded p-2" value={capMin} onChange={(e)=>setCapMin(Number(e.target.value))} />
              <span>min</span>
              <input type="number" min={0} max={59} className="w-24 border rounded p-2" value={capSec} onChange={(e)=>setCapSec(Number(e.target.value))} />
              <span>sec</span>
              <button disabled={loading} className="ml-2 bg-black text-white px-3 py-2 rounded disabled:opacity-50" onClick={submitCapability}>{loading?"Saving...":"Save"}</button>
            </div>
            {error && <p className="text-red-600 text-sm">{error}</p>}
          </div>
        )}

        {cur.key === "goal" && (
          <div className="mt-4 space-y-3">
            <ChatMessage role="system">Great. What’s your goal?</ChatMessage>
            <div className="flex flex-wrap gap-2">
              {[{label:"5K",v:5000},{label:"10K",v:10000},{label:"Half",v:21097},{label:"Marathon",v:42195}].map(d=> (
                <button key={d.v} onClick={()=>setGoalDistance(d.v)} className={`px-3 py-1 rounded border ${goalDistance===d.v?"bg-black text-white":""}`}>{d.label}</button>
              ))}
            </div>
            <label className="flex items-center gap-2"><input type="checkbox" checked={goalHasTime} onChange={e=>setGoalHasTime(e.target.checked)} /> Target finish time</label>
            {goalHasTime && (
              <div className="flex items-center gap-2">
                <input type="number" className="w-24 border rounded p-2" value={goalMin} onChange={e=>setGoalMin(Number(e.target.value))} />
                <span>min</span>
                <input type="number" className="w-24 border rounded p-2" value={goalSec} onChange={e=>setGoalSec(Number(e.target.value))} />
                <span>sec</span>
              </div>
            )}
            <div>
              <label className="block text-sm font-medium">Target date</label>
              <input type="date" className="border rounded p-2" value={goalDate} onChange={e=>setGoalDate(e.target.value)} />
            </div>
            <button disabled={loading} onClick={()=>checkFeas({ distance_m: goalDistance, target_time_sec: goalHasTime ? goalMin*60+goalSec : null, target_date: goalDate })} className="bg-black text-white px-3 py-2 rounded disabled:opacity-50">{loading?"Checking...":"Check feasibility"}</button>
            {error && <p className="text-red-600 text-sm">{error}</p>}
          </div>
        )}

        {cur.key === "feasibility" && feas && (
          <div className="mt-4 space-y-3">
            <ChatMessage role="system">Feasibility: {feas.feasible ? "Looks good!" : "Not quite on this timeline."}</ChatMessage>
            {!feas.feasible && (
              <div className="space-y-2">
                {feas.reasons.length>0 && <ul className="list-disc ml-6 text-sm text-gray-700">{feas.reasons.map((r,i)=>(<li key={i}>{r}</li>))}</ul>}
                {feas.tradeoffs.length>0 && (
                  <div>
                    <p className="font-medium text-sm">Trade-offs to consider:</p>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {feas.tradeoffs.map((t,i)=> (
                        <button key={i} className="border rounded px-3 py-1" onClick={()=>applyTradeoffApply(t)}>
                          {t.lever === "date" && `Push date by ${t.recommendation?.push_weeks} weeks`}
                          {t.lever === "time" && `Relax time by ${t.recommendation?.relax_seconds}s`}
                          {t.lever === "distance" && `Reduce distance to ${t.recommendation?.suggest_distance_m/1000} km`}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
            <div className="flex gap-2">
              <button disabled={loading || !feas.feasible} onClick={()=>generate(cur.goalId)} className="bg-black text-white px-3 py-2 rounded disabled:opacity-50">Generate plan</button>
              {!feas.feasible && <button className="border px-3 py-2 rounded" onClick={()=>applyTradeoffApply(feas.tradeoffs[0])}>Apply first suggestion</button>}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

