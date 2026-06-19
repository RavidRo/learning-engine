import babel from "@rolldown/plugin-babel";
import react, { reactCompilerPreset } from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";
import { defineConfig } from "vite-plus";

const backendOrigin = process.env["VITE_BACKEND_ORIGIN"] ?? "http://127.0.0.1:8765";

export default defineConfig({
  plugins: [
    react(),
    babel({ presets: [reactCompilerPreset()] }),
    VitePWA({
      includeAssets: ["favicon.ico", "favicon.svg", "apple-touch-icon.png"],
      devOptions: {
        enabled: true,
      },
      manifest: {
        background_color: "#fafafa",
        description: "Track learning interests and review fresh updates from saved sources.",
        display: "standalone",
        icons: [
          {
            src: "/pwa-192x192.png",
            sizes: "192x192",
            type: "image/png",
          },
          {
            src: "/pwa-512x512.png",
            sizes: "512x512",
            type: "image/png",
          },
          {
            purpose: "maskable",
            src: "/pwa-maskable-192x192.png",
            sizes: "192x192",
            type: "image/png",
          },
          {
            purpose: "maskable",
            src: "/pwa-maskable-512x512.png",
            sizes: "512x512",
            type: "image/png",
          },
        ],
        name: "Learning Engine",
        scope: "/",
        short_name: "Learning Engine",
        start_url: "/updates",
        theme_color: "#fafafa",
      },
      manifestFilename: "site.webmanifest",
      registerType: "prompt",
      workbox: {
        navigateFallback: "/index.html",
        navigateFallbackDenylist: [/^\/api\//],
      },
    }),
  ],
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
