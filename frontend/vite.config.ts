import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// During local dev, proxy /api to the backend so the SPA and API share an origin
// (mirrors the nginx setup used in production).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
