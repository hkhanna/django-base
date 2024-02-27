import { resolve } from "path";
import { loadEnv } from "vite";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

process.env = { ...process.env, ...loadEnv(null, process.cwd() + "/../") };

export default defineConfig({
  plugins: [react()],
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
