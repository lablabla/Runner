import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

interface ThemeCtx {
  isDark: boolean;
  toggle: () => void;
}

const Ctx = createContext<ThemeCtx>({ isDark: false, toggle: () => {} });

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem("hm_theme");
    if (saved) return saved === "dark";
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", isDark ? "dark" : "light");
    localStorage.setItem("hm_theme", isDark ? "dark" : "light");
  }, [isDark]);

  return <Ctx.Provider value={{ isDark, toggle: () => setIsDark((v) => !v) }}>{children}</Ctx.Provider>;
}

export const useTheme = () => useContext(Ctx);
