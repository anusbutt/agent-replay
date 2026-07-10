"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronDown, CircleAlert, GitFork, Loader2, ShieldCheck } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { forkRun, ApiRequestError, type RunDetail } from "@/lib/api";

function recordedSystemPrompt(run: RunDetail, forkStep: number): string {
  const step = run.steps.find(
    (s) => s.seq === forkStep && s.type === "llm_call",
  );
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
  const [showAdvanced, setShowAdvanced] = useState(false);
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
      setBusy(false);
    }
  }

  return (
    <Card id="fork">
      <CardHeader>
        <CardTitle>
          <GitFork className="size-4 text-violet-300" />
          Fork this run
        </CardTitle>
        <CardDescription>
          Replays the exact recorded context at the chosen step with your fix
          applied — one live model call, temperature 0.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-end gap-4">
          <label className="block">
            <span className="text-xs font-medium text-zinc-400">
              Fork at step
            </span>
            <Input
              type="number"
              min={1}
              value={forkStep}
              onChange={(e) => setForkStep(Number(e.target.value))}
              className="mt-1.5 w-24"
            />
          </label>
          {run.run_metadata.analysis?.failing_step != null && (
            <p className="pb-2 text-xs text-zinc-500">
              Analysis points at step {run.run_metadata.analysis.failing_step}.
            </p>
          )}
        </div>

        <label className="block">
          <span className="text-xs font-medium text-zinc-400">
            System prompt — edit to apply the fix
          </span>
          <Textarea
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            rows={7}
            className="mt-1.5 font-mono text-xs leading-relaxed"
          />
        </label>

        <div>
          <button
            type="button"
            onClick={() => setShowAdvanced((s) => !s)}
            className="flex cursor-pointer items-center gap-1 text-xs font-medium text-zinc-500 transition-colors hover:text-zinc-300"
          >
            <ChevronDown
              className={cn(
                "size-3.5 transition-transform duration-200",
                showAdvanced && "rotate-180",
              )}
            />
            Advanced
          </button>
          <AnimatePresence initial={false}>
            {showAdvanced && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.18, ease: "easeInOut" }}
                className="overflow-hidden"
              >
                <label className="mt-3 block">
                  <span className="text-xs font-medium text-zinc-400">
                    Temperature override
                  </span>
                  <Input
                    type="number"
                    step="0.1"
                    min={0}
                    max={2}
                    value={temperature}
                    onChange={(e) => setTemperature(e.target.value)}
                    placeholder="0"
                    className="mt-1.5 w-24"
                  />
                </label>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {error && (
          <p className="flex items-center gap-1.5 text-xs text-red-400">
            <CircleAlert className="size-3.5 shrink-0" />
            {error}
          </p>
        )}

        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={handleFork} disabled={busy}>
            {busy ? <Loader2 className="animate-spin" /> : <GitFork />}
            {busy ? "Forking…" : "Fork run"}
          </Button>
          <p className="flex items-center gap-1.5 text-[11px] text-zinc-500">
            <ShieldCheck className="size-3.5 text-emerald-400/70" />
            Sandboxed — no real tool ever executes in a fork.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
