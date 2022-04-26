const { resolve } = require('path');
const { loadEnv } = require('vite');


process.env = {...process.env, ...loadEnv(null, process.cwd() + '/../../')};

module.exports = {
  plugins: [],
  root: resolve('./src/'),
  base: '/static/',
  server: {
    host: 'localhost',
    port: process.env.VITE_PORT,
    strictPort: true,
    open: false,
    watch: {
      usePolling: true,
      disableGlobbing: false,
    },
  },
  resolve: {
    extensions: ['.js', '.json'],
  },
  build: {
    outDir: resolve('../static/'),
    assetsDir: '',
    manifest: true,
    emptyOutDir: true,
    target: 'es2015',
    rollupOptions: {
      input: {
        main: resolve('./src/js/main.js')
      },
      output: {
        chunkFileNames: undefined,
      },
    },
  },
};