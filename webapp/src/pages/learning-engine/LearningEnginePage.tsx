import { Toast } from "../../components/Toast";
import { AddInterestForm } from "./AddInterestForm";
import { BriefingSection } from "./BriefingSection";
import { HeroSection } from "./HeroSection";
import { InterestsPanel } from "./InterestsPanel";
import { TopNavigation } from "./TopNavigation";
import { useLearningEnginePageState } from "./useLearningEnginePageState";

export const LearningEnginePage = () => {
  const { state, actions } = useLearningEnginePageState();

  return (
    <>
      <main className="shell">
        <TopNavigation />
        <HeroSection
          enabledInterests={state.enabledInterests}
          sourcesTracked={state.sourcesTracked}
          totalInterests={state.interests.length}
        />

        <section className="workspace" aria-label="Interest workspace">
          <AddInterestForm onAddInterest={actions.addInterest} />
          <InterestsPanel
            interests={state.interests}
            isChecking={state.isChecking}
            isSaving={state.isSaving}
            loadError={state.loadError}
            onCheckUpdates={actions.checkUpdates}
            onRemoveInterest={actions.removeInterest}
            onSaveInterests={actions.saveInterests}
            onToggleInterest={actions.toggleInterest}
            updates={state.updates}
          />
        </section>

        <BriefingSection />
      </main>

      <Toast message={state.toast.message} visible={state.toast.visible} />
    </>
  );
};
