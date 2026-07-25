import { useSummary, useTrends } from "../api/hooks";
import {
  ChartCard,
  EfficiencyChart,
  LineTrend,
  SleepVsPerformanceChart,
  WeeklyMileageChart,
} from "../components/charts";
import { Badge, Card, Spinner, StatTile } from "../components/ui";
import { num } from "../format";
import { acwrColor } from "../palette";
import { useTheme } from "../theme";

export default function TrendsPage() {
  const { isDark } = useTheme();
  const { data, isLoading } = useTrends();
  const summary = useSummary();
  if (isLoading) return <Spinner />;
  const acwr = data?.acwr;
  const s = summary.data;

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Trends &amp; analysis</h1>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatTile label="Acute load (7d)" value={acwr?.acute ?? "–"} />
        <StatTile label="Chronic load (28d avg)" value={acwr?.chronic ?? "–"} />
        <StatTile
          label="ACWR"
          value={acwr?.ratio ?? "–"}
          accent={acwrColor(acwr?.zone ?? "", isDark)}
          sub={<Badge color={acwrColor(acwr?.zone ?? "", isDark)}>{acwr?.zone ?? "no data"}</Badge>}
        />
        <StatTile label="Avg HR (30d)" value={s?.avg_hr_30d != null ? `${num(s.avg_hr_30d, 0)} bpm` : "–"} />
        <StatTile label="Avg cadence (30d)" value={s?.avg_cadence_30d != null ? `${num(s.avg_cadence_30d, 0)} spm` : "–"} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartCard title="Weekly volume" subtitle="Distance per week (km)">
          <WeeklyMileageChart data={data?.weekly_mileage ?? []} />
        </ChartCard>
        <ChartCard title="Average heart rate" subtitle="Per run (bpm) — context for effort over time">
          <LineTrend data={data?.hr_cadence ?? []} dataKey="avg_hr" unit="bpm" seriesIndex={3} />
        </ChartCard>
        <ChartCard title="Cadence" subtitle="Per run (steps/min) — higher, steadier cadence is usually more efficient">
          <LineTrend data={data?.hr_cadence ?? []} dataKey="avg_cadence" unit="spm" seriesIndex={2} />
        </ChartCard>
        <ChartCard title="Resting heart rate" subtitle="Overnight (bpm) — a downward trend suggests improving fitness">
          <LineTrend data={data?.resting_hr ?? []} dataKey="resting_hr" unit="bpm" seriesIndex={1} />
        </ChartCard>
        <ChartCard title="Aerobic efficiency" subtitle="HR×pace index — a downward trend means improving fitness">
          <EfficiencyChart data={data?.aerobic_efficiency ?? []} />
        </ChartCard>
        <ChartCard title="Sleep vs run difficulty" subtitle="Do harder runs follow worse sleep?">
          <SleepVsPerformanceChart data={data?.sleep_vs_performance ?? []} />
        </ChartCard>
        <Card>
          <h3 className="mb-2 text-sm font-semibold">Reading these charts</h3>
          <ul className="list-inside list-disc space-y-1 text-sm text-ink-secondary">
            <li>
              <strong>ACWR</strong> compares your last 7 days of load to your 4-week average. Above 1.5 flags a
              spike in load and elevated injury risk.
            </li>
            <li>
              <strong>Aerobic efficiency</strong> multiplies average HR by pace. Running the same pace at a lower
              heart rate over time means your engine is getting fitter.
            </li>
            <li>
              <strong>Weekly volume</strong> should build gradually — avoid jumps larger than ~10% week to week.
            </li>
          </ul>
        </Card>
      </div>
    </div>
  );
}
