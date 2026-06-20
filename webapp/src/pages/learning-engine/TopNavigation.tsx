import { SignInButton, SignUpButton, UserButton, useAuth } from "@clerk/react";
import { useEffect, useMemo, useState } from "react";

import { type PageView } from "./types";

type TopNavigationProps = {
  onChangeView: (view: PageView) => void;
  view: PageView;
};

const navButtonClass = (view: PageView, target: PageView): string =>
  view === target ? "nav-button active" : "nav-button";

const Brand = () => (
  <a className="brand" href="/updates" aria-label="Signal Garden updates">
    <img
      className="brand-mark"
      src="/pwa-192x192.png"
      width="30"
      height="30"
      alt=""
      aria-hidden="true"
    />
    <span>Signal Garden</span>
  </a>
);

const NavLinks = ({ onChangeView, view }: TopNavigationProps) => (
  <div className="navlinks" aria-label="Sections">
    <button
      className={navButtonClass(view, "updates")}
      type="button"
      onClick={() => onChangeView("updates")}
    >
      Updates
    </button>
    <button
      className={navButtonClass(view, "collections")}
      type="button"
      onClick={() => onChangeView("collections")}
    >
      Collections
    </button>
    <button
      className={navButtonClass(view, "interests")}
      type="button"
      onClick={() => onChangeView("interests")}
    >
      Manage interests
    </button>
    <a href="#briefing">Briefing</a>
  </div>
);

const MpcIcon = () => (
  <span className="account-menu-icon" aria-hidden="true">
    MCP
  </span>
);

const mcpEndpoint = (): string => {
  if (typeof window === "undefined") {
    return "/mcp";
  }

  return new URL("/mcp", window.location.origin).toString();
};

const MpcTokenPage = () => {
  const { getToken } = useAuth();
  const [copyStatus, setCopyStatus] = useState<"idle" | "copied" | "error">("idle");
  const endpoint = useMemo(() => mcpEndpoint(), []);
  const setupCommand = `export LEARNING_ENGINE_CLERK_SESSION_TOKEN="<paste-token-here>"\n\ncodex mcp add learning-engine \\\n  --url ${endpoint} \\\n  --bearer-token-env-var LEARNING_ENGINE_CLERK_SESSION_TOKEN`;

  useEffect(() => {
    if (copyStatus === "idle") {
      return undefined;
    }

    const timeoutId = window.setTimeout(() => {
      setCopyStatus("idle");
    }, 1600);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [copyStatus]);

  const copySessionToken = async (): Promise<void> => {
    try {
      const token = await getToken();
      if (token === null) {
        setCopyStatus("error");
        return;
      }

      await navigator.clipboard.writeText(token);
      setCopyStatus("copied");
    } catch {
      setCopyStatus("error");
    }
  };

  return (
    <section className="mcp-token-page" aria-label="MCP setup">
      <div>
        <p className="section-label">Codex MCP</p>
        <h2>Connect your account</h2>
        <p>
          Copy the current Clerk session token, store it in your shell, and configure Codex to pass
          it as the MCP bearer token.
        </p>
      </div>

      <div className="mcp-token-actions">
        <button
          className="button primary compact"
          type="button"
          onClick={() => void copySessionToken()}
        >
          {copyStatus === "copied" ? "Copied token" : "Copy MCP token"}
        </button>
        {copyStatus === "error" ? (
          <span className="mcp-token-error">Sign in again before copying a token.</span>
        ) : null}
      </div>

      <div className="mcp-token-command" aria-label="Codex setup command">
        <pre>{setupCommand}</pre>
      </div>
    </section>
  );
};

const AuthControls = () => {
  const { isLoaded, isSignedIn } = useAuth();

  return (
    <div className="auth-controls" aria-label="Account">
      {isLoaded && isSignedIn ? (
        <UserButton>
          <UserButton.UserProfilePage label="MCP token" labelIcon={<MpcIcon />} url="mcp">
            <MpcTokenPage />
          </UserButton.UserProfilePage>
        </UserButton>
      ) : (
        <>
          <SignInButton mode="modal">
            <button className="button ghost compact" type="button">
              Sign in
            </button>
          </SignInButton>
          <SignUpButton mode="modal">
            <button className="button primary compact" type="button">
              Sign up
            </button>
          </SignUpButton>
        </>
      )}
    </div>
  );
};

export const TopNavigation = ({ onChangeView, view }: TopNavigationProps) => {
  return (
    <nav className="topbar" aria-label="Main navigation">
      <Brand />
      <NavLinks onChangeView={onChangeView} view={view} />
      <AuthControls />
    </nav>
  );
};
