import { resolve } from "path";
import { loadEnv } from "vite";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import svgLoader from "vite-svg-loader";

process.env = { ...process.env, ...loadEnv(null, process.cwd() + "/../") };

// HACK: Remove svgloader once Heroicons aren't loaded via Alpine in any projects that use this.

export default defineConfig({
  plugins: [react(), svgLoader({ defaultImport: "raw" })],
  root: resolve("./src/"),
  base: "/static/",
  server: {
    host: "localhost",
    port: process.env.VITE_PORT,
    origin: "http://localhost:" + process.env.VITE_PORT,
    strictPort: true,
    open: false,
    watch: {
      usePolling: true,
      disableGlobbing: false,
    },
  },
  resolve: {
    extensions: [".js", ".json", ".ts", ".jsx", ".tsx"],
    alias: {
      "@": resolve("./src/js/"),
    },
  },
  build: {
    outDir: resolve("./dist/"),
    assetsDir: "",
    manifest: "manifest.json",
    emptyOutDir: true,
    target: "es2017",
    rollupOptions: {
      input: {
        main: resolve("./src/js/main.js"),
        react: resolve("./src/js/react.tsx"),
      },
      output: {
        chunkFileNames: undefined,
      },
    },
  },
});
