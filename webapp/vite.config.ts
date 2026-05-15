import babel from "@rolldown/plugin-babel";
import react, { reactCompilerPreset } from "@vitejs/plugin-react";
import { defineConfig } from "vite-plus";

const backendOrigin = process.env["VITE_BACKEND_ORIGIN"] ?? "http://127.0.0.1:8765";

export default defineConfig({
  plugins: [react(), babel({ presets: [reactCompilerPreset()] })],
  lint: {
    ignorePatterns: ["dist/**"],
    options: {
      denyWarnings: true,
      reportUnusedDisableDirectives: "deny",
      typeAware: true,
      typeCheck: true,
    },
  },
  fmt: {
    ignorePatterns: ["dist/**"],
    sortPackageJson: true,
  },
  server: {
    proxy: {
      "/api": backendOrigin,
    },
  },
});
