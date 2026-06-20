import { ClerkProvider } from "@clerk/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App";
import { clerkPublishableKey } from "./config";
import { registerPwa } from "./pwa";
import { queryClient } from "./queryClient";
import "./styles.css";

const rootElement = document.getElementById("root");

if (rootElement === null) {
  throw new Error("Root element not found");
}

registerPwa();

const publishableKey = clerkPublishableKey();

const app = (
  <QueryClientProvider client={queryClient}>
    <App />
  </QueryClientProvider>
);

const missingClerkConfiguration = (
  <main className="shell">
    <section className="panel auth-gate" aria-label="Missing Clerk configuration">
      <p className="section-label">Configuration</p>
      <h1>Clerk is not configured</h1>
      <p className="subtitle">
        Set VITE_CLERK_PUBLISHABLE_KEY before starting the webapp so users can sign in.
      </p>
    </section>
  </main>
);

createRoot(rootElement).render(
  <StrictMode>
    {publishableKey === null ? (
      missingClerkConfiguration
    ) : (
      <ClerkProvider publishableKey={publishableKey}>{app}</ClerkProvider>
    )}
  </StrictMode>,
);
