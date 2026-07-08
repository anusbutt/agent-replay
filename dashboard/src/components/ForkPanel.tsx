"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { forkRun, ApiRequestError, type RunDetail } from "@/lib/api";

function recordedSystemPrompt(run: RunDetail, forkStep: number): string {
  const step = run.steps.find((s) => s.seq === forkStep && s.type === "llm_call");
  const messages = step?.input?.messages as
    | { role?: string; content?: string }[]
    | undefined;
  return messages?.find((m) => m.role === "system")?.content ?? "";
}

export function ForkPanel({ run }: { run: RunDetail }) {
  const router = useRouter();
  const suggestedStep = run.run_metadata.analysis?.failing_step ?? 1;
  const [forkStep, setForkStep] = useState(suggestedStep);
  const [systemPrompt, setSystemPrompt] = useState(
    () =>
      recordedSystemPrompt(run, suggestedStep) +
      (run.run_metadata.analysis?.suggested_fix
        ? `\n\n${run.run_metadata.analysis.suggested_fix}`
        : ""),
  );
  const [temperature, setTemperature] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFork() {
    setBusy(true);
    setError(null);
    try {
      const fork = await forkRun(run.id, {
        fork_step: forkStep,
        modification: { system_prompt: systemPrompt },
        temperature: temperature === "" ? null : Number(temperature),
      });
      router.push(`/runs/${fork.id}`);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.detail : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
      <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
        Fork this run
      </h3>
      <p className="mt-1 text-xs text-zinc-500">
        Reconstructs the recorded context at the chosen step, applies your
        fix, and calls the model live once. No real tool runs.
      </p>

      <div className="mt-4 space-y-3">
        <label className="block text-xs font-medium text-zinc-600 dark:text-zinc-400">
          Fork at step (seq)
          <input
            type="number"
            min={1}
            value={forkStep}
            onChange={(e) => setForkStep(Number(e.target.value))}
            className="mt-1 block w-24 rounded border border-zinc-300 px-2 py-1 text-sm dark:border-zinc-700 dark:bg-zinc-900"
          />
        </label>

        <label className="block text-xs font-medium text-zinc-600 dark:text-zinc-400">
          System prompt (edit to apply the fix)
          <textarea
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            rows={6}
            className="mt-1 block w-full rounded border border-zinc-300 px-2 py-1 font-mono text-xs dark:border-zinc-700 dark:bg-zinc-900"
          />
        </label>

        <label className="block text-xs font-medium text-zinc-600 dark:text-zinc-400">
          Temperature override (optional — default 0)
          <input
            type="number"
            step="0.1"
            min={0}
            max={2}
            value={temperature}
            onChange={(e) => setTemperature(e.target.value)}
            placeholder="0"
            className="mt-1 block w-24 rounded border border-zinc-300 px-2 py-1 text-sm dark:border-zinc-700 dark:bg-zinc-900"
          />
        </label>

        {error && (
          <p className="text-xs text-red-600 dark:text-red-400">{error}</p>
        )}

        <button
          type="button"
          onClick={handleFork}
          disabled={busy}
          className="rounded bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-700 disabled:opacity-50"
        >
          {busy ? "Forking…" : "Fork run"}
        </button>
      </div>
    </div>
  );
}
