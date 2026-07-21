// Chart colors resolved from the active theme. Recharts needs concrete color
// strings, so we mirror the CSS tokens here and select by theme.
export interface ChartTheme {
  series: string[];
  grid: string;
  axis: string;
  text: string;
  status: { good: string; warning: string; serious: string; critical: string };
  surface: string;
}

const light: ChartTheme = {
  series: ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"],
  grid: "#e1e0d9",
  axis: "#c3c2b7",
  text: "#52514e",
  status: { good: "#0ca30c", warning: "#fab219", serious: "#ec835a", critical: "#d03b3b" },
  surface: "#fcfcfb",
};

const dark: ChartTheme = {
  series: ["#3987e5", "#d95926", "#199e70", "#c98500"],
  grid: "#2c2c2a",
  axis: "#383835",
  text: "#c3c2b7",
  status: { good: "#0ca30c", warning: "#fab219", serious: "#ec835a", critical: "#d03b3b" },
  surface: "#1a1a19",
};

export function chartTheme(isDark: boolean): ChartTheme {
  return isDark ? dark : light;
}

// ACWR zone -> status color mapping.
export function acwrColor(zone: string, isDark: boolean): string {
  const t = chartTheme(isDark).status;
  switch (zone) {
    case "optimal":
      return t.good;
    case "caution":
      return t.warning;
    case "high-risk":
      return t.critical;
    default:
      return chartTheme(isDark).axis;
  }
}
