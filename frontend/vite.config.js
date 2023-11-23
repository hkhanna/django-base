import "vite/modulepreload-polyfill";
const { resolve } = require("path");
const { loadEnv } = require("vite");
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
const svgLoader = require("vite-svg-loader");

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
  },
  build: {
    outDir: resolve("./dist/"),
    assetsDir: "",
    manifest: true,
    emptyOutDir: true,
    target: "es2017",
    rollupOptions: {
      input: {
        main: resolve("./src/js/main.js"),
      },
      output: {
        chunkFileNames: undefined,
      },
    },
  },
});
