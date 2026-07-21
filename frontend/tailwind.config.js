/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["selector", '[data-theme="dark"]'],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      // Surfaces and ink map to the dataviz reference palette via CSS variables
      // declared in index.css, so light/dark swap in one place.
      colors: {
        surface: "var(--surface-1)",
        plane: "var(--page-plane)",
        ink: "var(--text-primary)",
        "ink-secondary": "var(--text-secondary)",
        muted: "var(--muted)",
        hairline: "var(--gridline)",
        brand: "var(--series-1)",
      },
      fontFamily: {
        sans: ["system-ui", "-apple-system", "Segoe UI", "sans-serif"],
      },
    },
  },
  plugins: [],
};
