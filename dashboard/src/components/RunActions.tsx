"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { CircleAlert, Loader2, Microscope, Radar } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  analyzeRun,
  detectSweep,
  ApiRequestError,
  type RunStatus,
} from "@/lib/api";

export function RunActions({
  runId,
  status,
}: {
  runId: string;
  status: RunStatus;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState<"detect" | "analyze" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run(kind: "detect" | "analyze") {
    setBusy(kind);
    setError(null);
    try {
      if (kind === "detect") await detectSweep([runId]);
      else await analyzeRun(runId);
      router.refresh();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.detail : String(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-2">
        <Button
          variant="glass"
          size="sm"
          onClick={() => run("detect")}
          disabled={busy !== null}
        >
          {busy === "detect" ? (
            <Loader2 className="animate-spin" />
          ) : (
            <Radar />
          )}
          {busy === "detect" ? "Sweeping…" : "Run detection"}
        </Button>

        {status === "flagged" && (
          <Button
            variant="glass"
            size="sm"
            onClick={() => run("analyze")}
            disabled={busy !== null}
          >
            {busy === "analyze" ? (
              <Loader2 className="animate-spin" />
            ) : (
              <Microscope />
            )}
            {busy === "analyze" ? "Analyzing…" : "Analyze root cause"}
          </Button>
        )}
      </div>
      {error && (
        <p className="flex items-center gap-1.5 text-xs text-red-400">
          <CircleAlert className="size-3.5 shrink-0" />
          {error}
        </p>
      )}
    </div>
  );
}
