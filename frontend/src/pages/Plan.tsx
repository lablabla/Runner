import { useRef, useState } from "react";

import { useCreateWorkout, useDeleteWorkout, useImportPlanPdf, usePlan } from "../api/hooks";
import { Badge, Button, Card, ErrorNote, Spinner } from "../components/ui";
import { shortDate } from "../format";

const TYPES = ["easy", "tempo", "intervals", "long", "recovery", "rest", "race"];

export default function PlanPage() {
  const { data, isLoading } = usePlan();
  const create = useCreateWorkout();
  const del = useDeleteWorkout();
  const importPdf = useImportPlanPdf();
  const fileRef = useRef<HTMLInputElement>(null);

  const [date, setDate] = useState("");
  const [type, setType] = useState("easy");
  const [title, setTitle] = useState("");
  const [distanceKm, setDistanceKm] = useState("");

  if (isLoading) return <Spinner />;

  const add = (e: React.FormEvent) => {
    e.preventDefault();
    create.mutate(
      {
        date,
        workout_type: type,
        title: title || null,
        distance_target_m: distanceKm ? Number(distanceKm) * 1000 : null,
      },
      {
        onSuccess: () => {
          setTitle("");
          setDistanceKm("");
        },
      },
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Training plan</h1>
        <div>
          <input
            ref={fileRef}
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) importPdf.mutate(f);
            }}
          />
          <Button variant="ghost" onClick={() => fileRef.current?.click()} disabled={importPdf.isPending}>
            {importPdf.isPending ? "Importing…" : "Import Runna PDF"}
          </Button>
        </div>
      </div>

      {importPdf.isError && <ErrorNote message={(importPdf.error as Error).message} />}
      {importPdf.isSuccess && (
        <Card>
          <p className="text-sm text-ink-secondary">
            Imported {importPdf.data.length} workout(s) from the PDF. Review and edit below — parsing is
            best-effort, so double-check dates and distances.
          </p>
        </Card>
      )}

      <Card>
        <h3 className="mb-3 text-sm font-semibold">Add a workout manually</h3>
        <form onSubmit={add} className="grid gap-3 sm:grid-cols-5">
          <input
            type="date"
            required
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="rounded-lg border border-hairline bg-plane px-3 py-2 text-sm"
          />
          <select
            value={type}
            onChange={(e) => setType(e.target.value)}
            className="rounded-lg border border-hairline bg-plane px-3 py-2 text-sm capitalize"
          >
            {TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          <input
            placeholder="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="rounded-lg border border-hairline bg-plane px-3 py-2 text-sm sm:col-span-2"
          />
          <input
            placeholder="km"
            type="number"
            step="0.1"
            value={distanceKm}
            onChange={(e) => setDistanceKm(e.target.value)}
            className="rounded-lg border border-hairline bg-plane px-3 py-2 text-sm"
          />
          <Button type="submit" disabled={create.isPending} className="sm:col-span-5">
            Add workout
          </Button>
        </form>
      </Card>

      <Card>
        <h3 className="mb-3 text-sm font-semibold">Scheduled workouts</h3>
        {!data?.length ? (
          <p className="text-sm text-muted">No planned workouts yet.</p>
        ) : (
          <ul className="divide-y divide-hairline">
            {data.map((w) => (
              <li key={w.id} className="flex items-center gap-3 py-2">
                <span className="w-16 text-sm text-muted">{shortDate(w.date)}</span>
                <Badge>{w.workout_type}</Badge>
                <span className="min-w-0 flex-1 truncate text-sm">
                  {w.title || w.description || "—"}
                  {w.distance_target_m ? (
                    <span className="ml-2 text-muted">{(w.distance_target_m / 1000).toFixed(1)} km</span>
                  ) : null}
                </span>
                <span className="text-xs text-muted">{w.source}</span>
                <button
                  onClick={() => del.mutate(w.id)}
                  className="text-xs text-muted hover:text-ink"
                  aria-label="Delete"
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
