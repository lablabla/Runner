import { useState } from "react";
import { Link } from "react-router-dom";

import { useActivities } from "../api/hooks";
import type { Activity } from "../api/types";
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

      {/* Mobile: card list */}
      <ul className="space-y-2 sm:hidden">
        {data?.map((a) => <MobileRow key={a.id} a={a} />)}
        {!data?.length && <EmptyNote />}
      </ul>

      {/* Desktop: table */}
      <Card className="hidden sm:block">
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
                <th className="py-2 text-right">Diff.</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((a) => (
                <tr key={a.id} className="border-b border-hairline last:border-0 hover:bg-plane">
                  <td className="whitespace-nowrap py-2 pr-3 text-muted">{dateTime(a.start_time)}</td>
                  <td className="py-2 pr-3">
                    <Link to={`/activities/${a.id}`} className="font-medium text-ink hover:text-brand">
                      {a.name || a.sport_type}
                    </Link>{" "}
                    {a.is_runna && <Badge>Runna</Badge>}
                    <span className="ml-1 text-xs text-muted">{a.source}</span>
                  </td>
                  <td className="whitespace-nowrap py-2 pr-3 text-right tabular-nums">{km(a.distance_m)}</td>
                  <td className="whitespace-nowrap py-2 pr-3 text-right tabular-nums">{pace(a.avg_pace_s_per_km)}</td>
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
          {!data?.length && <EmptyNote />}
        </div>
      </Card>
    </div>
  );
}

function MobileRow({ a }: { a: Activity }) {
  return (
    <li>
      <Link to={`/activities/${a.id}`}>
        <Card className="flex items-center gap-3 p-3 active:bg-plane">
          <span
            className="w-9 shrink-0 text-center text-lg font-semibold tabular-nums"
            style={{ color: "var(--series-1)" }}
          >
            {a.difficulty_score != null ? Math.round(a.difficulty_score) : "–"}
          </span>
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-medium">
              {a.name || a.sport_type} {a.is_runna && <Badge>Runna</Badge>}
            </div>
            <div className="text-xs text-muted">{dateTime(a.start_time)}</div>
          </div>
          <div className="shrink-0 text-right text-sm">
            <div className="tabular-nums">{km(a.distance_m)}</div>
            <div className="text-xs text-muted tabular-nums">
              {pace(a.avg_pace_s_per_km)}
              {a.weather?.apparent_temp_c != null ? ` · ${num(a.weather.apparent_temp_c, 0)}°` : ""}
            </div>
          </div>
        </Card>
      </Link>
    </li>
  );
}

function EmptyNote() {
  return <p className="py-6 text-center text-sm text-muted">No activities found.</p>;
}
