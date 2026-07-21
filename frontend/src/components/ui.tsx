import type { ReactNode } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={`rounded-xl border border-hairline bg-surface p-4 shadow-sm ${className}`}
    >
      {children}
    </div>
  );
}

export function StatTile({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  accent?: string;
}) {
  return (
    <Card>
      <div className="text-xs uppercase tracking-wide text-muted">{label}</div>
      <div className="mt-1 text-2xl font-semibold" style={accent ? { color: accent } : undefined}>
        {value}
      </div>
      {sub && <div className="mt-1 text-sm text-ink-secondary">{sub}</div>}
    </Card>
  );
}

export function Button({
  children,
  onClick,
  type = "button",
  disabled,
  variant = "primary",
  className = "",
}: {
  children: ReactNode;
  onClick?: () => void;
  type?: "button" | "submit";
  disabled?: boolean;
  variant?: "primary" | "ghost";
  className?: string;
}) {
  const base =
    "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium transition disabled:opacity-50";
  const styles =
    variant === "primary"
      ? "bg-brand text-white hover:opacity-90"
      : "border border-hairline text-ink hover:bg-plane";
  return (
    <button type={type} onClick={onClick} disabled={disabled} className={`${base} ${styles} ${className}`}>
      {children}
    </button>
  );
}

export function Badge({ children, color }: { children: ReactNode; color?: string }) {
  return (
    <span
      className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
      style={{
        color: color ?? "var(--text-secondary)",
        backgroundColor: "color-mix(in srgb, currentColor 14%, transparent)",
      }}
    >
      {children}
    </span>
  );
}

export function Spinner({ label = "Loading…" }: { label?: string }) {
  return <div className="p-8 text-center text-ink-secondary">{label}</div>;
}

export function ErrorNote({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-hairline bg-surface p-3 text-sm text-ink-secondary">
      <span style={{ color: "var(--status-critical)" }}>●</span> {message}
    </div>
  );
}
