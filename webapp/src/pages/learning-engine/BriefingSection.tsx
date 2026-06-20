import { useEffect, useState } from "react";

const briefingPrompt = "Read my Signal Garden interests and prepare an evening briefing.";

export const BriefingSection = () => {
  const [didCopy, setDidCopy] = useState(false);

  useEffect(() => {
    if (!didCopy) {
      return undefined;
    }

    const timeoutId = window.setTimeout(() => {
      setDidCopy(false);
    }, 1400);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [didCopy]);

  const copyPrompt = async (): Promise<void> => {
    await navigator.clipboard.writeText(briefingPrompt);
    setDidCopy(true);
  };

  return (
    <section id="briefing" className="briefing">
      <div className="briefing-header">
        <div>
          <p className="section-label">Briefing utility</p>
          <h2>Evening review prompt</h2>
          <p>Use the current interest graph as briefing context.</p>
        </div>
        <button className="button ghost compact" type="button" onClick={() => void copyPrompt()}>
          {didCopy ? "Copied" : "Copy"}
        </button>
      </div>
      <div className="prompt-card">
        <p>{briefingPrompt}</p>
      </div>
    </section>
  );
};
