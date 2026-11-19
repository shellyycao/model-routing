"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ImportDialog } from "@/components/ImportDialog";
import { newId, requestPlan, setPendingDraft } from "@/lib/client/session";

const EXAMPLES = [
  { label: "Predict customer churn", goal: "I want to predict customer churn from a CSV, evaluate the model, explain important features, and write a report." },
  { label: "Literature review", goal: "I want to review research papers, extract evidence, check citations, and write a literature review." },
  { label: "Parallel data analysis", goal: "I want to clean my dataset, run exploratory analysis and visualization in parallel, and summarize the results." },
];

export default function HomePage() {
  const router = useRouter();
  const [goal, setGoal] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [importOpen, setImportOpen] = useState(false);

  const generate = async () => {
    if (!goal.trim()) {
      setError("Describe what you want the workflow to do.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const response = await requestPlan(goal);
      setPendingDraft({ kind: "planner", response });
      router.push("/studio?pending=1");
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  };

  return (
    <main className="min-h-[calc(100vh-4rem)] bg-[radial-gradient(ellipse_56%_52%_at_53%_25%,#43326370,transparent_75%),radial-gradient(ellipse_45%_35%_at_15%_87%,#22334c50,transparent_80%)] px-5 pb-16 pt-[8vh]">
      <div className="mx-auto max-w-[1030px]">
        <span className="eyebrow">EXPLAINABLE AI WORKFLOWS</span>
        <h1 className="my-5 text-[clamp(44px,5.2vw,78px)] font-semibold leading-[1.06] tracking-[-0.045em]">
          Your workflow.
          <br />
          <span className="text-[#b7a6ff]">Smarter decisions.</span>
        </h1>
        <p className="max-w-[750px] text-[clamp(16px,1.7vw,20px)] leading-relaxed text-[#c0bdcf]">
          Design new workflows or improve existing ones, with model choices you can trace back to saved benchmark evidence.
        </p>
        <p className="mt-2 max-w-[750px] text-sm text-soft">
          Early preview: drafts come from built-in templates, and evidence panels show only results that were actually measured.
        </p>

        <div className="mt-14 flex flex-col gap-10 md:flex-row md:items-start md:gap-12">
          <section aria-labelledby="create-title" className="min-w-0 md:flex-[1.4]">
            <h2 id="create-title" className="mb-3 text-sm font-bold text-[#eeeafc]">
              Create a workflow
            </h2>
            <div className="rounded-[17px] border border-[#5d5478] bg-[#1b1c2c99] p-5 pb-3.5 shadow-[0_24px_60px_#0002] focus-within:border-accent">
              <label htmlFor="goal" className="sr-only">
                Describe your goal
              </label>
              <textarea
                id="goal"
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) generate();
                }}
                placeholder="e.g. I want to predict customer churn from a CSV, explain the key drivers, evaluate fairness, and prepare a report."
                className="min-h-[120px] w-full resize-y bg-transparent text-base leading-relaxed text-[#edeaf9] outline-none placeholder:text-[#88859d]"
              />
              <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
                <span className="text-xs text-[#8c899d]">Template planner (mock) · no AI model is called yet</span>
                <button type="button" className="btn-primary px-6 text-[15px]" onClick={generate} disabled={busy}>
                  {busy ? "Generating…" : "Generate Workflow ↗"}
                </button>
              </div>
            </div>
            {error && (
              <p role="alert" className="mt-3 text-sm text-danger">
                {error}
              </p>
            )}
            <div className="mt-6 flex flex-wrap gap-2.5" aria-label="Example prompts">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex.label}
                  type="button"
                  onClick={() => setGoal(ex.goal)}
                  className="rounded-full border border-[#494559] px-4 py-3 text-sm text-[#c2bdd3] hover:border-accent hover:text-ink"
                >
                  {ex.label}
                </button>
              ))}
            </div>
          </section>

          <section aria-labelledby="improve-title" className="min-w-0 border-t border-[#484258] pt-8 md:flex-1 md:border-l md:border-t-0 md:pl-11 md:pt-0">
            <h2 id="improve-title" className="mb-3 text-sm font-bold text-[#eeeafc]">
              Improve my workflow
            </h2>
            <h3 className="mb-4 text-[26px] font-semibold tracking-tight">Make it better.</h3>
            <p className="text-[15px] leading-relaxed text-[#a9a8ba]">
              Open something you have saved, import an existing JSON or YAML definition, or start on an empty canvas. Every import is previewed before it is applied.
            </p>
            <div className="mt-4 flex flex-col items-start">
              <Link href="/library" className="py-3 text-[17px] font-semibold text-[#c0b2ff] hover:text-[#ddd4ff]">
                Open a saved workflow →
              </Link>
              <button type="button" onClick={() => setImportOpen(true)} className="py-3 text-[17px] font-semibold text-[#c0b2ff] hover:text-[#ddd4ff]">
                Import JSON / YAML →
              </button>
              <Link href="/studio?new=1" className="py-3 text-[17px] font-semibold text-[#c0b2ff] hover:text-[#ddd4ff]">
                Start with an empty canvas →
              </Link>
            </div>
          </section>
        </div>
      </div>
      <ImportDialog
        open={importOpen}
        onClose={() => setImportOpen(false)}
        fallbackId={newId("wf")}
        onImport={(workflow, warnings, sourceName) => {
          setPendingDraft({ kind: "import", workflow, warnings, sourceName });
          router.push("/studio?pending=1");
        }}
      />
    </main>
  );
}
