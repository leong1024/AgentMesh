import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const ONE_HOUR_MS = 3_600_000;

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8080",
        changeOrigin: true,
        timeout: ONE_HOUR_MS,
        proxyTimeout: ONE_HOUR_MS,
        configure: (proxy) => {
          proxy.on("proxyRes", (_proxyRes, _req, res) => {
            // Hints to intermediaries not to buffer (helps some SSE setups)
            res.setHeader("X-Accel-Buffering", "no");
            res.setHeader("Cache-Control", "no-cache");
          });
        },
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
  },
});
