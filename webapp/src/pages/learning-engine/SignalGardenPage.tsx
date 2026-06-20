import { SignInButton, SignUpButton } from "@clerk/react";
import { useState } from "react";

import { Toast } from "../../components/Toast";
import { useIsOffline } from "../../useOnlineStatus";
import { usePwaUpdate } from "../../usePwaUpdate";
import { AppStatusBanner } from "./AppStatusBanner";
import { BriefingSection } from "./BriefingSection";
import { CollectionsPage } from "./CollectionsPage";
import { InterestEditor } from "./InterestEditor";
import { InterestsPanel } from "./InterestsPanel";
import { TopNavigation } from "./TopNavigation";
import { UpdatesPage } from "./UpdatesPage";
import { useSignalGardenPageState } from "./useSignalGardenPageState";

type SignalGardenState = ReturnType<typeof useSignalGardenPageState>["state"];
type SignalGardenActions = ReturnType<typeof useSignalGardenPageState>["actions"];

type PageViewContentProps = {
  actions: SignalGardenActions;
  editingInterest: SignalGardenState["interests"][number] | null;
  editorKey: string;
  onCancelEdit: () => void;
  onEditInterest: (id: string) => void;
  onCreateInterest: SignalGardenActions["addInterest"];
  state: SignalGardenState;
};

const SignedOutPage = ({ isAuthLoaded }: { isAuthLoaded: boolean }) => (
  <main className="shell auth-page">
    <section className="auth-page-brand" aria-label="Signal Garden">
      <img
        className="brand-mark"
        src="/pwa-192x192.png"
        width="30"
        height="30"
        alt=""
        aria-hidden="true"
      />
      <span>Signal Garden</span>
    </section>

    <section className="panel auth-gate" aria-label="Account required">
      <p className="section-label">Account required</p>
      <h1>{isAuthLoaded ? "Sign in to open Signal Garden" : "Preparing your account"}</h1>
      <p className="subtitle">
        {isAuthLoaded
          ? "Create an account or sign in to load your personal interests, updates, and saved collections."
          : "Checking the active session before loading your workspace."}
      </p>
      {isAuthLoaded ? (
        <div className="auth-page-actions">
          <SignInButton mode="modal">
            <button className="button ghost" type="button">
              Sign in
            </button>
          </SignInButton>
          <SignUpButton mode="modal">
            <button className="button primary" type="button">
              Sign up
            </button>
          </SignUpButton>
        </div>
      ) : null}
    </section>
  </main>
);

const PageViewContent = ({
  actions,
  editingInterest,
  editorKey,
  onCancelEdit,
  onCreateInterest,
  onEditInterest,
  state,
}: PageViewContentProps) => {
  if (state.view === "interests") {
    return (
      <section className="workspace" aria-label="Interest workspace">
        <InterestsPanel
          interests={state.interests}
          isExporting={state.isExporting}
          isImporting={state.isImporting}
          isOffline={state.isConnectionUnavailable}
          loadError={state.loadError}
          onEditInterest={onEditInterest}
          onExportInterests={actions.exportInterests}
          onImportInterests={actions.importInterests}
          onRemoveInterest={actions.removeInterest}
          onToggleInterest={actions.toggleInterest}
          saveError={state.saveError}
          saveStatus={state.saveStatus}
        />
        <InterestEditor
          isOffline={state.isConnectionUnavailable}
          interest={editingInterest}
          key={editorKey}
          onCancelEdit={onCancelEdit}
          onCreateInterest={onCreateInterest}
          onUpdateInterest={actions.updateInterest}
        />
      </section>
    );
  }

  if (state.view === "collections") {
    return (
      <CollectionsPage
        collections={state.collections}
        collectionsError={state.collectionsError}
        isLoadingCollections={state.isLoadingCollections}
        isRemovingSavedUpdate={state.isRemovingSavedUpdate}
        onRemoveSavedUpdate={actions.removeSavedUpdate}
      />
    );
  }

  return (
    <UpdatesPage
      collections={state.collections}
      days={state.updateDays}
      isChecking={state.isChecking}
      isOffline={state.isConnectionUnavailable}
      isRemovingSavedUpdate={state.isRemovingSavedUpdate}
      isSavingToCollection={state.isSavingToCollection}
      onDaysChange={state.setUpdateDays}
      onRefresh={actions.checkUpdates}
      onRemoveSavedUpdate={actions.removeSavedUpdate}
      onSaveUpdateToCollection={actions.saveUpdateToCollection}
      onTrackUpdateCheckout={actions.trackUpdateCheckout}
      updates={state.updates}
      updatesError={state.updatesError}
    />
  );
};

export const SignalGardenPage = () => {
  const isBrowserOffline = useIsOffline();
  const pwaUpdate = usePwaUpdate();
  const { state, actions } = useSignalGardenPageState({ isBrowserOffline });
  const [editingInterestId, setEditingInterestId] = useState<string | null>(null);
  const [newEditorVersion, setNewEditorVersion] = useState(0);
  const editingInterest =
    state.interests.find((interest) => interest.id === editingInterestId) ?? null;
  const editorKey = editingInterest === null ? `new-${newEditorVersion}` : editingInterest.id;

  const handleCreateInterest: typeof actions.addInterest = (draft) => {
    actions.addInterest(draft);
    setEditingInterestId(null);
    setNewEditorVersion((version) => version + 1);
  };

  if (!state.isAuthenticated) {
    return <SignedOutPage isAuthLoaded={state.isAuthLoaded} />;
  }

  return (
    <>
      <main className="shell">
        <TopNavigation onChangeView={actions.changeView} view={state.view} />
        <AppStatusBanner
          isConnectionUnavailable={state.isConnectionUnavailable}
          onRefreshUpdate={pwaUpdate.refreshUpdate}
          updateAvailable={pwaUpdate.updateAvailable}
        />

        <PageViewContent
          actions={actions}
          editingInterest={editingInterest}
          editorKey={editorKey}
          onCancelEdit={() => setEditingInterestId(null)}
          onCreateInterest={handleCreateInterest}
          onEditInterest={setEditingInterestId}
          state={state}
        />

        <BriefingSection />
      </main>

      <Toast message={state.toast.message} visible={state.toast.visible} />
    </>
  );
};
