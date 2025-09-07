"use client";
import { useEffect, useState } from "react";
import { apiCurrentPlan } from "@/lib/api";

export default function CalendarPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [workouts, setWorkouts] = useState<any[]>([]);

  useEffect(() => {
    (async () => {
      try {
        const plan = await apiCurrentPlan();
        setWorkouts(plan.workouts || []);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Your Plan</h1>
      {loading && <p>Loading…</p>}
      {error && <p className="text-red-600">{error}</p>}
      {!loading && !error && (
        <div className="bg-white border rounded divide-y">
          {workouts.map(w => (
            <div key={w.id} className="p-3 flex items-center justify-between">
              <div>
                <div className="font-medium">{new Date(w.wdate).toDateString()}</div>
                <div className="text-sm text-gray-600">{w.wtype} · {w.target_distance_m ? `${(w.target_distance_m/1000).toFixed(1)} km` : "—"}</div>
              </div>
              {w.is_key && <span className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded">Key</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

