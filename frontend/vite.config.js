const { resolve } = require("path");
const { loadEnv } = require("vite");

process.env = { ...process.env, ...loadEnv(null, process.cwd() + "/../") };

module.exports = {
  plugins: [],
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
    extensions: [".js", ".json", ".ts"],
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
};
