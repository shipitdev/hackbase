import { defineConfig } from "vite";

export default defineConfig({
  esbuild: { jsx: "automatic" },
  server: {
    strictPort: true,
    proxy: { "/api": { target: "http://127.0.0.1:8000", timeout: 300000, proxyTimeout: 300000 } },
  },
  preview: { proxy: { "/api": "http://127.0.0.1:8000" } },
});
