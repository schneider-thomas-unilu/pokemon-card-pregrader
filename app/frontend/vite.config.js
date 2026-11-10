import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    watch: {
      usePolling: true,
      interval: 500,
    },
    hmr: {
      clientPort: Number(process.env.VITE_HMR_CLIENT_PORT ?? "5173"),
    },
    proxy: {
      "/api": process.env.API_PROXY_TARGET ?? "http://localhost:8000",
    },
  },
});
