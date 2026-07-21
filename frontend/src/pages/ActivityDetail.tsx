import { Link, useParams } from "react-router-dom";

import { useActivity, useAnalyseActivity } from "../api/hooks";
import { ChartCard, DifficultyBreakdown } from "../components/charts";
import { Badge, Button, Card, ErrorNote, Spinner, StatTile } from "../components/ui";
import { dateTime, duration, km, num, pace } from "../format";

export default function ActivityDetailPage() {
  const { id } = useParams();
  const activityId = Number(id);
  const { data: a, isLoading } = useActivity(activityId);
  const analyse = useAnalyseActivity();

  if (isLoading || !a) return <Spinner />;

  return (
    <div className="space-y-5">
      <div>
        <Link to="/activities" className="text-sm text-brand hover:underline">
          ← Activities
        </Link>
        <h1 className="mt-1 text-xl font-semibold">
          {a.name || a.sport_type} {a.is_runna && <Badge>Runna</Badge>}
        </h1>
        <p className="text-sm text-muted">
          {dateTime(a.start_time)} · <span className="capitalize">{a.sport_type}</span> · {a.source}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatTile label="Distance" value={km(a.distance_m)} />
        <StatTile label="Time" value={duration(a.duration_s)} />
        <StatTile label="Avg pace" value={pace(a.avg_pace_s_per_km)} />
        <StatTile
          label="Difficulty"
          value={a.difficulty_score != null ? Math.round(a.difficulty_score) : "–"}
          accent="var(--series-1)"
        />
        <StatTile label="Avg HR" value={num(a.avg_hr)} sub={a.max_hr ? `max ${num(a.max_hr)}` : undefined} />
        <StatTile label="Elevation" value={a.elevation_gain_m != null ? `${num(a.elevation_gain_m)} m` : "–"} />
        <StatTile label="Aerobic TE" value={num(a.aerobic_te, 1)} />
        <StatTile
          label="Weather"
          value={a.weather?.apparent_temp_c != null ? `${num(a.weather.apparent_temp_c, 0)}°` : "–"}
          sub={a.weather?.summary ?? undefined}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartCard title="Why was it hard?" subtitle="Difficulty component contributions (0–100)">
          <DifficultyBreakdown activity={a} />
        </ChartCard>

        {a.weather && (
          <Card>
            <h3 className="mb-3 text-sm font-semibold">Conditions</h3>
            <dl className="grid grid-cols-2 gap-y-2 text-sm">
              <Detail label="Temperature" value={a.weather.temp_c != null ? `${num(a.weather.temp_c, 0)}°C` : "–"} />
              <Detail
                label="Feels like"
                value={a.weather.apparent_temp_c != null ? `${num(a.weather.apparent_temp_c, 0)}°C` : "–"}
              />
              <Detail label="Humidity" value={a.weather.humidity_pct != null ? `${num(a.weather.humidity_pct)}%` : "–"} />
              <Detail
                label="Wind"
                value={a.weather.wind_speed_kmh != null ? `${num(a.weather.wind_speed_kmh)} km/h` : "–"}
              />
              <Detail label="Precip" value={a.weather.precip_mm != null ? `${num(a.weather.precip_mm, 1)} mm` : "–"} />
              <Detail label="Summary" value={a.weather.summary ?? "–"} />
            </dl>
          </Card>
        )}
      </div>

      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold">Coach analysis</h3>
            <p className="text-xs text-ink-secondary">Uses your configured LLM to explain this run.</p>
          </div>
          <Button onClick={() => analyse.mutate(activityId)} disabled={analyse.isPending} variant="ghost">
            {analyse.isPending ? "Analysing…" : "Analyse run"}
          </Button>
        </div>
        {analyse.isError && <div className="mt-3"><ErrorNote message={(analyse.error as Error).message} /></div>}
        {analyse.data && (
          <p className="mt-3 whitespace-pre-wrap text-sm text-ink-secondary">{analyse.data.content}</p>
        )}
      </Card>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt className="text-muted">{label}</dt>
      <dd className="text-right font-medium">{value}</dd>
    </>
  );
}
