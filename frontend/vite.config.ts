import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// Dev server proxies /api to the backend. Defaults to the deployed Render backend, but can
// be overridden by setting VITE_API_BASE (e.g. http://localhost:8000) in a .env file.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "VITE_");
  const target = env.VITE_API_BASE || "https://meeting-intelligence-platform.onrender.com";
  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        "/api": { target, changeOrigin: true, secure: true },
      },
    },
  };
});
