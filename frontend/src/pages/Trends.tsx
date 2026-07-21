import { useTrends } from "../api/hooks";
import { ChartCard, EfficiencyChart, SleepVsPerformanceChart, WeeklyMileageChart } from "../components/charts";
import { Badge, Card, Spinner, StatTile } from "../components/ui";
import { acwrColor } from "../palette";
import { useTheme } from "../theme";

export default function TrendsPage() {
  const { isDark } = useTheme();
  const { data, isLoading } = useTrends();
  if (isLoading) return <Spinner />;
  const acwr = data?.acwr;

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
        <StatTile label="Sweet spot" value="0.8–1.3" sub="target ACWR range" />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartCard title="Weekly volume" subtitle="Distance per week (km)">
          <WeeklyMileageChart data={data?.weekly_mileage ?? []} />
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
