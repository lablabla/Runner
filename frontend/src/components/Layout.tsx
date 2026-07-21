import { NavLink, useNavigate } from "react-router-dom";

import { useAuth } from "../auth";
import { useSync } from "../api/hooks";
import { useTheme } from "../theme";

const NAV = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/activities", label: "Activities" },
  { to: "/trends", label: "Trends" },
  { to: "/plan", label: "Plan" },
  { to: "/insights", label: "Insights" },
  { to: "/settings", label: "Settings" },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const { signOut } = useAuth();
  const { isDark, toggle } = useTheme();
  const navigate = useNavigate();
  const sync = useSync();

  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-10 border-b border-hairline bg-surface/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-3">
          <span className="text-lg font-semibold">🏃 HM Tracker</span>
          <nav className="hidden gap-1 md:flex">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `rounded-lg px-3 py-1.5 text-sm ${
                    isActive ? "bg-plane font-medium text-ink" : "text-ink-secondary hover:text-ink"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-2">
            <button
              onClick={() => sync.mutate()}
              disabled={sync.isPending}
              className="rounded-lg border border-hairline px-3 py-1.5 text-sm hover:bg-plane disabled:opacity-50"
            >
              {sync.isPending ? "Syncing…" : "Sync now"}
            </button>
            <button
              onClick={toggle}
              className="rounded-lg border border-hairline px-2 py-1.5 text-sm hover:bg-plane"
              aria-label="Toggle theme"
            >
              {isDark ? "☀️" : "🌙"}
            </button>
            <button
              onClick={() => {
                signOut();
                navigate("/login");
              }}
              className="rounded-lg border border-hairline px-3 py-1.5 text-sm hover:bg-plane"
            >
              Sign out
            </button>
          </div>
        </div>
        {/* Mobile nav */}
        <nav className="flex gap-1 overflow-x-auto px-4 pb-2 md:hidden">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `whitespace-nowrap rounded-lg px-3 py-1.5 text-sm ${
                  isActive ? "bg-plane font-medium" : "text-ink-secondary"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        {sync.isError && (
          <div className="px-4 pb-2 text-xs" style={{ color: "var(--status-critical)" }}>
            Sync failed: {(sync.error as Error).message}
          </div>
        )}
        {sync.isSuccess && sync.data.errors.length > 0 && (
          <div className="px-4 pb-2 text-xs" style={{ color: "var(--status-warning)" }}>
            Sync completed with issues: {sync.data.errors.join("; ")}
          </div>
        )}
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
    </div>
  );
}
