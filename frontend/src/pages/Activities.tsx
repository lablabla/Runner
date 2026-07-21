import { useState } from "react";
import { Link } from "react-router-dom";

import { useActivities } from "../api/hooks";
import { Badge, Card, Spinner } from "../components/ui";
import { dateTime, km, num, pace } from "../format";

export default function ActivitiesPage() {
  const [runnaOnly, setRunnaOnly] = useState(false);
  const { data, isLoading } = useActivities({ runna_only: runnaOnly });

  if (isLoading) return <Spinner />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Activities</h1>
        <label className="flex items-center gap-2 text-sm text-ink-secondary">
          <input type="checkbox" checked={runnaOnly} onChange={(e) => setRunnaOnly(e.target.checked)} />
          Runna only
        </label>
      </div>

      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-hairline text-left text-xs uppercase text-muted">
                <th className="py-2 pr-3">Date</th>
                <th className="py-2 pr-3">Run</th>
                <th className="py-2 pr-3 text-right">Distance</th>
                <th className="py-2 pr-3 text-right">Pace</th>
                <th className="py-2 pr-3 text-right">Avg HR</th>
                <th className="py-2 pr-3 text-right">Temp</th>
                <th className="py-2 text-right">Difficulty</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((a) => (
                <tr key={a.id} className="border-b border-hairline last:border-0 hover:bg-plane">
                  <td className="py-2 pr-3 text-muted">{dateTime(a.start_time)}</td>
                  <td className="py-2 pr-3">
                    <Link to={`/activities/${a.id}`} className="font-medium text-ink hover:text-brand">
                      {a.name || a.sport_type}
                    </Link>{" "}
                    {a.is_runna && <Badge>Runna</Badge>}
                    <span className="ml-1 text-xs text-muted">{a.source}</span>
                  </td>
                  <td className="py-2 pr-3 text-right tabular-nums">{km(a.distance_m)}</td>
                  <td className="py-2 pr-3 text-right tabular-nums">{pace(a.avg_pace_s_per_km)}</td>
                  <td className="py-2 pr-3 text-right tabular-nums">{num(a.avg_hr)}</td>
                  <td className="py-2 pr-3 text-right tabular-nums">
                    {a.weather?.apparent_temp_c != null ? `${num(a.weather.apparent_temp_c, 0)}°` : "–"}
                  </td>
                  <td className="py-2 text-right font-semibold tabular-nums" style={{ color: "var(--series-1)" }}>
                    {a.difficulty_score != null ? Math.round(a.difficulty_score) : "–"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!data?.length && <p className="py-6 text-center text-sm text-muted">No activities found.</p>}
        </div>
      </Card>
    </div>
  );
}
