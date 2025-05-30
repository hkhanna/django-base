import path from "path";
import { loadEnv } from "vite";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

process.env = { ...process.env, ...loadEnv(null, process.cwd() + "/../") };

export default defineConfig({
  plugins: [react()],
  root: path.resolve("./src/"),
  base: "/static/",
  server: {
    host: true,
    port: process.env.VITE_PORT,
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
      "@": path.resolve("./src/"),
    },
  },
  build: {
    outDir: path.resolve("./dist/"),
    assetsDir: "",
    manifest: "manifest.json",
    emptyOutDir: true,
    target: "es2017",
    rollupOptions: {
      input: {
        inertia: path.resolve("./src/inertia.tsx"),
      },
      output: {
        chunkFileNames: undefined,
      },
    },
  },
});
