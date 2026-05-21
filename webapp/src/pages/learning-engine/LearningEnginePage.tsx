import { Toast } from "../../components/Toast";
import { BriefingSection } from "./BriefingSection";
import { HeroSection } from "./HeroSection";
import { InterestEditor } from "./InterestEditor";
import { InterestsPanel } from "./InterestsPanel";
import { TopNavigation } from "./TopNavigation";
import { UpdatesPage } from "./UpdatesPage";
import { useLearningEnginePageState } from "./useLearningEnginePageState";
import { useState } from "react";

export const LearningEnginePage = () => {
  const { state, actions } = useLearningEnginePageState();
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

  return (
    <>
      <main className="shell">
        <TopNavigation onChangeView={actions.changeView} view={state.view} />
        <HeroSection
          enabledInterests={state.enabledInterests}
          sourcesTracked={state.sourcesTracked}
          totalInterests={state.interests.length}
        />

        {state.view === "interests" ? (
          <section className="workspace" aria-label="Interest workspace">
            <InterestEditor
              interest={editingInterest}
              key={editorKey}
              onCancelEdit={() => setEditingInterestId(null)}
              onCreateInterest={handleCreateInterest}
              onUpdateInterest={actions.updateInterest}
            />
            <InterestsPanel
              interests={state.interests}
              loadError={state.loadError}
              onEditInterest={setEditingInterestId}
              onRemoveInterest={actions.removeInterest}
              onToggleInterest={actions.toggleInterest}
              saveError={state.saveError}
              saveStatus={state.saveStatus}
            />
          </section>
        ) : (
          <UpdatesPage
            days={state.updateDays}
            isChecking={state.isChecking}
            onDaysChange={state.setUpdateDays}
            onRefresh={actions.checkUpdates}
            updates={state.updates}
            updatesError={state.updatesError}
          />
        )}

        <BriefingSection />
      </main>

      <Toast message={state.toast.message} visible={state.toast.visible} />
    </>
  );
};
