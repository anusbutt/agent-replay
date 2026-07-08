"use client";

import { useState } from "react";
import type { Step } from "@/lib/api";

const TYPE_STYLES: Record<Step["type"], string> = {
  llm_call: "border-l-violet-500",
  tool_call: "border-l-sky-500",
  state_change: "border-l-zinc-400",
};

function JsonBlock({ label, value }: { label: string; value: unknown }) {
  return (
    <div>
      <div className="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
        {label}
      </div>
      <pre className="mt-1 max-h-96 overflow-auto rounded bg-zinc-50 p-3 text-xs text-zinc-800 dark:bg-zinc-900 dark:text-zinc-200">
        {JSON.stringify(value, null, 2)}
      </pre>
    </div>
  );
}

export function TimelineStep({
  step,
  parentOrigin = false,
}: {
  step: Step;
  parentOrigin?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={`border-l-4 ${TYPE_STYLES[step.type]} rounded-r bg-white pl-4 pr-3 py-3 shadow-sm dark:bg-zinc-950`}
    >
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        className="flex w-full items-center justify-between gap-2 text-left"
      >
        <span className="flex items-center gap-2">
          <span className="font-mono text-xs text-zinc-400">
            seq {step.seq}
          </span>
          <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
            {step.type}
          </span>
          {parentOrigin && (
            <span className="rounded bg-zinc-200 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
              parent
            </span>
          )}
        </span>
        <span className="flex items-center gap-2 text-xs text-zinc-500">
          {step.latency_ms != null && <span>{step.latency_ms}ms</span>}
          {step.tokens_in != null && step.tokens_out != null && (
            <span>
              {step.tokens_in}→{step.tokens_out} tok
            </span>
          )}
          <span>{expanded ? "▲" : "▼"}</span>
        </span>
      </button>

      {expanded && (
        <div className="mt-3 space-y-3">
          <JsonBlock label="input (verbatim)" value={step.input} />
          <JsonBlock label="output (verbatim)" value={step.output} />
        </div>
      )}
    </div>
  );
}
