import { Link } from "react-router-dom";

import { useActivities, useIntegrations, useSummary, useTrends } from "../api/hooks";
import { ChartCard, SleepVsPerformanceChart, WeeklyMileageChart } from "../components/charts";
import { Badge, Card, Spinner, StatTile } from "../components/ui";
import { dateTime, km, num, pace } from "../format";
import { acwrColor } from "../palette";
import { useTheme } from "../theme";

export default function Dashboard() {
  const { isDark } = useTheme();
  const summary = useSummary();
  const trends = useTrends();
  const activities = useActivities();
  const integrations = useIntegrations();

  if (summary.isLoading) return <Spinner />;

  const s = summary.data;
  const acwr = s?.acwr;
  const recent = activities.data?.slice(0, 5) ?? [];
  const hasGarmin = integrations.data?.some((i) => i.provider === "garmin");

  return (
    <div className="space-y-6">
      {!hasGarmin && (
        <Card>
          <p className="text-sm text-ink-secondary">
            👋 Connect your Garmin account on the{" "}
            <Link to="/settings" className="text-brand hover:underline">
              Settings
            </Link>{" "}
            page, then hit <strong>Sync now</strong> to pull in your runs and health data.
          </p>
        </Card>
      )}

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatTile label="This week" value={`${num(s?.this_week_km, 1)} km`} />
        <StatTile label="Total runs" value={s?.total_runs ?? 0} sub={`${num(s?.total_distance_km, 0)} km all-time`} />
        <StatTile
          label="Training load (ACWR)"
          value={acwr?.ratio ?? "–"}
          sub={<Badge color={acwrColor(acwr?.zone ?? "", isDark)}>{acwr?.zone ?? "no data"}</Badge>}
          accent={acwrColor(acwr?.zone ?? "", isDark)}
        />
        <StatTile label="Readiness" value={s?.latest_readiness != null ? num(s.latest_readiness, 0) : "–"} sub="latest" />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartCard title="Weekly volume" subtitle="Distance per week (km)">
          <WeeklyMileageChart data={trends.data?.weekly_mileage ?? []} />
        </ChartCard>
        <ChartCard title="Sleep vs run difficulty" subtitle="Each dot is a run; lower-left = poor sleep, easy run">
          <SleepVsPerformanceChart data={trends.data?.sleep_vs_performance ?? []} />
        </ChartCard>
      </div>

      <Card>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold">Recent runs</h3>
          <Link to="/activities" className="text-sm text-brand hover:underline">
            View all
          </Link>
        </div>
        {recent.length === 0 ? (
          <p className="text-sm text-muted">No activities yet.</p>
        ) : (
          <ul className="divide-y divide-hairline">
            {recent.map((a) => (
              <li key={a.id}>
                <Link to={`/activities/${a.id}`} className="flex items-center gap-3 py-2 hover:opacity-80">
                  <span className="w-10 text-right text-lg font-semibold tabular-nums" style={{ color: "var(--series-1)" }}>
                    {a.difficulty_score != null ? Math.round(a.difficulty_score) : "–"}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium">
                      {a.name || a.sport_type} {a.is_runna && <Badge>Runna</Badge>}
                    </div>
                    <div className="text-xs text-muted">{dateTime(a.start_time)}</div>
                  </div>
                  <div className="text-right text-sm text-ink-secondary">
                    <div>{km(a.distance_m)}</div>
                    <div className="text-xs text-muted">{pace(a.avg_pace_s_per_km)}</div>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
