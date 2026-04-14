import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@maxhub/max-ui": path.resolve(__dirname, "src/max/maxUiShim.tsx"),
    },
  },
});
