export function km(distance_m: number | null | undefined): string {
  if (distance_m == null) return "–";
  return `${(distance_m / 1000).toFixed(2)} km`;
}

export function pace(sPerKm: number | null | undefined): string {
  if (!sPerKm) return "–";
  const m = Math.floor(sPerKm / 60);
  const s = Math.round(sPerKm % 60);
  return `${m}:${s.toString().padStart(2, "0")}/km`;
}

export function duration(seconds: number | null | undefined): string {
  if (!seconds) return "–";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.round(seconds % 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m ${s.toString().padStart(2, "0")}s`;
}

export function hoursFromSeconds(seconds: number | null | undefined): string {
  if (!seconds) return "–";
  return `${(seconds / 3600).toFixed(1)}h`;
}

export function shortDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function dateTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function num(v: number | null | undefined, digits = 0, unit = ""): string {
  if (v == null) return "–";
  return `${v.toFixed(digits)}${unit}`;
}
