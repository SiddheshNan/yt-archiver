import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";
import { nodePolyfills } from "vite-plugin-node-polyfills";
import markdownRawPlugin from "vite-raw-plugin";
import path from "path";

const PORT = 3039;

export default defineConfig({
  build: {
    chunkSizeWarningLimit: 100,
    target: 'es2019' // or 'es2020' to avoid Object.hasOwn
    // rollupOptions: {
    //   onwarn(warning, warn) {
    //     if (warning.code === "MODULE_LEVEL_DIRECTIVE") {
    //       return;
    //     }
    //     warn(warning);
    //   },
    // },
  },

  resolve: {
    alias: [
      {
        find: /^~(.+)/,
        replacement: path.join(process.cwd(), "node_modules/$1"),
      },
      {
        find: /^src(.+)/,
        replacement: path.join(process.cwd(), "src/$1"),
      },
      { find: "@", replacement: "/src" }
    ],
  },

  plugins: [
    react(),
    nodePolyfills(),
    markdownRawPlugin({
      fileRegex: /\.md$/,
    }),
  ],
  server: { port: PORT, host: true },
  preview: { port: PORT, host: true },
  esbuild: {
    loader: "jsx",
  },
  optimizeDeps: {
    esbuildOptions: {
      loader: {
        ".js": "jsx",
      },
      define: {
        global: "globalThis",
      },
    },
  },
});
