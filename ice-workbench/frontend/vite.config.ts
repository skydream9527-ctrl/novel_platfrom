import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "src") },
  },
  server: {
    port: 5173,
    proxy: {
      // /api/v1/ws/conversations/* upgrades through here, so this single proxy
      // entry needs ws:true to forward both HTTP + WebSocket upgrade frames.
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        ws: true,
      },
    },
  },
  build: {
    chunkSizeWarningLimit: 600,
    modulePreload: {
      // Only preload chunks needed for the chunk currently being requested,
      // not the full transitive graph. Keeps first paint lean.
      resolveDependencies: () => [],
    },
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) return undefined;
          // React core (always needed for first paint)
          if (
            id.includes("/react/") ||
            id.includes("/react-dom/") ||
            id.includes("/scheduler/") ||
            id.includes("/react-router-dom/") ||
            id.includes("/react-router/") ||
            id.includes("/@remix-run/")
          ) {
            return "vendor-react";
          }
          // Markdown stack (only loaded inside chat / guide; large)
          if (
            id.includes("/react-markdown/") ||
            id.includes("/remark-") ||
            id.includes("/rehype-") ||
            id.includes("/micromark") ||
            id.includes("/mdast-") ||
            id.includes("/unist-") ||
            id.includes("/hast-") ||
            id.includes("/unified") ||
            id.includes("/vfile") ||
            id.includes("/decode-named") ||
            id.includes("/character-entities") ||
            id.includes("/property-information") ||
            id.includes("/space-separated") ||
            id.includes("/comma-separated") ||
            id.includes("/zwitch") ||
            id.includes("/longest-streak")
          ) {
            return "vendor-markdown";
          }
          // Syntax highlighter (huge: refractor + prism langs)
          if (id.includes("/react-syntax-highlighter/") || id.includes("/refractor/") || id.includes("/highlight.js/") || id.includes("/lowlight/")) {
            return "vendor-highlighter";
          }
          if (id.includes("/dompurify/")) {
            return "vendor-dompurify";
          }
          if (id.includes("/axios/")) {
            return "vendor-axios";
          }
          if (id.includes("/zustand/") || id.includes("/use-sync-external-store/")) {
            return "vendor-zustand";
          }
          return "vendor-misc";
        },
      },
    },
  },
});
