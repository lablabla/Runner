import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type ThemeMode = "light" | "dark" | "system";

interface ThemeCtx {
  mode: ThemeMode;
  isDark: boolean; // resolved value actually applied
  setMode: (m: ThemeMode) => void;
  cycle: () => void; // light -> dark -> system -> light
}

const Ctx = createContext<ThemeCtx>({
  mode: "system",
  isDark: false,
  setMode: () => {},
  cycle: () => {},
});

const MQ = "(prefers-color-scheme: dark)";

function readSavedMode(): ThemeMode {
  const saved = localStorage.getItem("hm_theme");
  return saved === "light" || saved === "dark" || saved === "system" ? saved : "system";
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<ThemeMode>(readSavedMode);
  const [systemDark, setSystemDark] = useState(() => window.matchMedia(MQ).matches);

  // Follow the OS setting live — only affects the UI while mode === "system".
  useEffect(() => {
    const mq = window.matchMedia(MQ);
    const handler = (e: MediaQueryListEvent) => setSystemDark(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  const isDark = mode === "system" ? systemDark : mode === "dark";

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", isDark ? "dark" : "light");
    localStorage.setItem("hm_theme", mode);
  }, [isDark, mode]);

  const value = useMemo<ThemeCtx>(
    () => ({
      mode,
      isDark,
      setMode,
      cycle: () =>
        setMode((m) => (m === "light" ? "dark" : m === "dark" ? "system" : "light")),
    }),
    [mode, isDark],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export const useTheme = () => useContext(Ctx);
