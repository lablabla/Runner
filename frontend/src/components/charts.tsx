import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";

import type { Activity, Trends } from "../api/types";
import { shortDate } from "../format";
import { chartTheme } from "../palette";
import { useTheme } from "../theme";
import { Card } from "./ui";

function TooltipBox({ rows }: { rows: [string, string][] }) {
  return (
    <div className="rounded-lg border border-hairline bg-surface px-3 py-2 text-xs shadow">
      {rows.map(([k, v]) => (
        <div key={k} className="flex justify-between gap-4">
          <span className="text-muted">{k}</span>
          <span className="font-medium text-ink" style={{ fontVariantNumeric: "tabular-nums" }}>
            {v}
          </span>
        </div>
      ))}
    </div>
  );
}

export function ChartCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <Card>
      <div className="mb-3">
        <h3 className="text-sm font-semibold text-ink">{title}</h3>
        {subtitle && <p className="text-xs text-ink-secondary">{subtitle}</p>}
      </div>
      <div style={{ width: "100%", height: 240 }}>{children}</div>
    </Card>
  );
}

// Weekly training volume — magnitude, so one sequential hue (blue).
export function WeeklyMileageChart({ data }: { data: Trends["weekly_mileage"] }) {
  const { isDark } = useTheme();
  const t = chartTheme(isDark);
  if (!data.length) return <Empty />;
  return (
    <ResponsiveContainer>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
        <CartesianGrid stroke={t.grid} vertical={false} />
        <XAxis dataKey="week" tick={{ fill: t.text, fontSize: 11 }} tickLine={false} axisLine={{ stroke: t.axis }} />
        <YAxis tick={{ fill: t.text, fontSize: 11 }} tickLine={false} axisLine={false} />
        <Tooltip
          cursor={{ fill: t.grid, opacity: 0.4 }}
          content={({ active, payload }) =>
            active && payload?.length ? (
              <TooltipBox
                rows={[
                  ["Week", String(payload[0].payload.week)],
                  ["Distance", `${payload[0].payload.distance_km} km`],
                  ["Runs", String(payload[0].payload.runs)],
                  ["Time", `${payload[0].payload.duration_h} h`],
                ]}
              />
            ) : null
          }
        />
        <Bar dataKey="distance_km" fill={t.series[0]} radius={[4, 4, 0, 0]} maxBarSize={44} />
      </BarChart>
    </ResponsiveContainer>
  );
}

// Aerobic efficiency index over time — single series line (lower is fitter).
export function EfficiencyChart({ data }: { data: Trends["aerobic_efficiency"] }) {
  const { isDark } = useTheme();
  const t = chartTheme(isDark);
  if (!data.length) return <Empty />;
  const shaped = data.map((d) => ({ ...d, label: shortDate(d.date) }));
  return (
    <ResponsiveContainer>
      <LineChart data={shaped} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
        <CartesianGrid stroke={t.grid} vertical={false} />
        <XAxis dataKey="label" tick={{ fill: t.text, fontSize: 11 }} tickLine={false} axisLine={{ stroke: t.axis }} />
        <YAxis tick={{ fill: t.text, fontSize: 11 }} tickLine={false} axisLine={false} domain={["auto", "auto"]} />
        <Tooltip
          content={({ active, payload }) =>
            active && payload?.length ? (
              <TooltipBox
                rows={[
                  ["Date", String(payload[0].payload.label)],
                  ["Efficiency", String(payload[0].payload.efficiency_index)],
                ]}
              />
            ) : null
          }
        />
        <Line
          type="monotone"
          dataKey="efficiency_index"
          stroke={t.series[0]}
          strokeWidth={2}
          dot={{ r: 3, fill: t.series[0], strokeWidth: 0 }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

// Sleep score vs run difficulty — relationship, single-series scatter.
export function SleepVsPerformanceChart({ data }: { data: Trends["sleep_vs_performance"] }) {
  const { isDark } = useTheme();
  const t = chartTheme(isDark);
  if (!data.length) return <Empty />;
  return (
    <ResponsiveContainer>
      <ScatterChart margin={{ top: 8, right: 8, bottom: 4, left: -16 }}>
        <CartesianGrid stroke={t.grid} />
        <XAxis
          type="number"
          dataKey="sleep_score"
          name="Sleep"
          domain={[0, 100]}
          tick={{ fill: t.text, fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: t.axis }}
          label={{ value: "Sleep score", position: "insideBottom", offset: -2, fill: t.text, fontSize: 11 }}
        />
        <YAxis
          type="number"
          dataKey="difficulty_score"
          name="Difficulty"
          domain={[0, 100]}
          tick={{ fill: t.text, fontSize: 11 }}
          tickLine={false}
          axisLine={false}
        />
        <ZAxis range={[50, 50]} />
        <Tooltip
          cursor={{ stroke: t.axis }}
          content={({ active, payload }) =>
            active && payload?.length ? (
              <TooltipBox
                rows={[
                  ["Date", shortDate(payload[0].payload.date)],
                  ["Sleep", String(payload[0].payload.sleep_score)],
                  ["Difficulty", String(payload[0].payload.difficulty_score)],
                ]}
              />
            ) : null
          }
        />
        <Scatter data={data} fill={t.series[0]} />
      </ScatterChart>
    </ResponsiveContainer>
  );
}

const COMPONENT_LABELS: Record<string, string> = {
  intensity: "Intensity",
  duration: "Duration",
  elevation: "Elevation",
  heat: "Heat",
  readiness: "Fatigue",
};

// Difficulty component breakdown for a single activity — magnitude, one hue,
// with direct value labels.
export function DifficultyBreakdown({ activity }: { activity: Activity }) {
  const { isDark } = useTheme();
  const t = chartTheme(isDark);
  const bd = activity.difficulty_breakdown;
  if (!bd) return <Empty label="No difficulty data" />;
  const rows = Object.entries(bd)
    .filter(([k]) => k in COMPONENT_LABELS)
    .map(([k, v]) => ({ name: COMPONENT_LABELS[k], value: v as number }));
  if (!rows.length) return <Empty label="No difficulty data" />;
  return (
    <ResponsiveContainer>
      <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 32, bottom: 4, left: 8 }}>
        <XAxis type="number" domain={[0, 100]} hide />
        <YAxis
          type="category"
          dataKey="name"
          tick={{ fill: t.text, fontSize: 12 }}
          tickLine={false}
          axisLine={false}
          width={70}
        />
        <Bar dataKey="value" fill={t.series[0]} radius={[0, 4, 4, 0]} maxBarSize={22} label={{ position: "right", fill: t.text, fontSize: 11 }}>
          {rows.map((_, i) => (
            <Cell key={i} fill={t.series[0]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

function Empty({ label = "No data yet" }: { label?: string }) {
  return <div className="flex h-full items-center justify-center text-sm text-muted">{label}</div>;
}
