import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test-utils/setup.ts"],
  },
  resolve: {
    alias: {
      "@maxhub/max-ui": path.resolve(__dirname, "src/max/maxUiShim.tsx"),
    },
  },
});
