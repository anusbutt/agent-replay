"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { analyzeRun, detectSweep, ApiRequestError, type RunStatus } from "@/lib/api";

export function RunActions({ runId, status }: { runId: string; status: RunStatus }) {
  const router = useRouter();
  const [busy, setBusy] = useState<"detect" | "analyze" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function runDetect() {
    setBusy("detect");
    setError(null);
    try {
      await detectSweep([runId]);
      router.refresh();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.detail : String(err));
    } finally {
      setBusy(null);
    }
  }

  async function runAnalyze() {
    setBusy("analyze");
    setError(null);
    try {
      await analyzeRun(runId);
      router.refresh();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.detail : String(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex gap-2">
        <button
          type="button"
          onClick={runDetect}
          disabled={busy !== null}
          className="rounded border border-zinc-300 px-3 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
        >
          {busy === "detect" ? "Running sweep…" : "Run detection sweep"}
        </button>
        {status === "flagged" && (
          <button
            type="button"
            onClick={runAnalyze}
            disabled={busy !== null}
            className="rounded border border-zinc-300 px-3 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
          >
            {busy === "analyze" ? "Analyzing…" : "Analyze"}
          </button>
        )}
      </div>
      {error && <p className="text-xs text-red-600 dark:text-red-400">{error}</p>}
    </div>
  );
}
