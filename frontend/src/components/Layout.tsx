import { NavLink, useNavigate } from "react-router-dom";

import { useSync } from "../api/hooks";
import { useAuth } from "../auth";
import { useTheme, type ThemeMode } from "../theme";

const NAV = [
  { to: "/", label: "Dashboard", icon: "📊", end: true },
  { to: "/activities", label: "Activities", icon: "🏃" },
  { to: "/trends", label: "Trends", icon: "📈" },
  { to: "/plan", label: "Plan", icon: "🗓️" },
  { to: "/insights", label: "Insights", icon: "✨" },
  { to: "/settings", label: "Settings", icon: "⚙️" },
];

const THEME_ICON: Record<ThemeMode, string> = { light: "☀️", dark: "🌙", system: "🖥️" };
const THEME_NEXT: Record<ThemeMode, ThemeMode> = { light: "dark", dark: "system", system: "light" };
const THEME_LABEL: Record<ThemeMode, string> = { light: "Light", dark: "Dark", system: "System" };

const iconBtn =
  "inline-flex items-center gap-1.5 whitespace-nowrap rounded-lg border border-hairline px-2.5 py-1.5 text-sm hover:bg-plane disabled:opacity-50";

export default function Layout({ children }: { children: React.ReactNode }) {
  const { signOut } = useAuth();
  const { mode, cycle } = useTheme();
  const navigate = useNavigate();
  const sync = useSync();

  return (
    <div className="min-h-full pb-[calc(4.5rem+env(safe-area-inset-bottom))] md:pb-0">
      <header className="sticky top-0 z-20 border-b border-hairline bg-surface/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-3">
          <span className="whitespace-nowrap text-base font-semibold sm:text-lg">🏃 HM&nbsp;Tracker</span>

          {/* Desktop primary nav */}
          <nav className="ml-2 hidden gap-1 md:flex">
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

          <div className="ml-auto flex items-center gap-1.5">
            <button onClick={() => sync.mutate()} disabled={sync.isPending} className={iconBtn}>
              <span aria-hidden>{sync.isPending ? "⏳" : "↻"}</span>
              <span className="hidden sm:inline">{sync.isPending ? "Syncing…" : "Sync"}</span>
            </button>
            <button
              onClick={cycle}
              className={iconBtn}
              title={`Theme: ${THEME_LABEL[mode]} — tap for ${THEME_LABEL[THEME_NEXT[mode]]}`}
              aria-label={`Theme: ${THEME_LABEL[mode]}. Switch to ${THEME_LABEL[THEME_NEXT[mode]]}`}
            >
              <span aria-hidden>{THEME_ICON[mode]}</span>
              <span className="hidden lg:inline">{THEME_LABEL[mode]}</span>
            </button>
            <button
              onClick={() => {
                signOut();
                navigate("/login");
              }}
              className={iconBtn}
              aria-label="Sign out"
            >
              <span aria-hidden>⎋</span>
              <span className="hidden sm:inline">Sign out</span>
            </button>
          </div>
        </div>

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

      {/* Mobile bottom tab bar */}
      <nav className="fixed inset-x-0 bottom-0 z-20 border-t border-hairline bg-surface/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden">
        <div className="mx-auto flex max-w-6xl">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex flex-1 flex-col items-center gap-0.5 py-2 text-[11px] ${
                  isActive ? "font-medium text-brand" : "text-ink-secondary"
                }`
              }
            >
              <span className="text-lg leading-none" aria-hidden>
                {item.icon}
              </span>
              {item.label}
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  );
}
