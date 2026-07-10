"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowRightLeft,
  Brain,
  ChevronDown,
  Clock,
  Coins,
  Wrench,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Step } from "@/lib/api";

const TYPE_CONFIG: Record<
  Step["type"],
  { icon: React.ReactNode; ring: string; label: string }
> = {
  llm_call: {
    icon: <Brain className="size-3.5 text-violet-300" />,
    ring: "bg-violet-500/15 ring-violet-400/30",
    label: "LLM call",
  },
  tool_call: {
    icon: <Wrench className="size-3.5 text-sky-300" />,
    ring: "bg-sky-500/15 ring-sky-400/30",
    label: "Tool call",
  },
  state_change: {
    icon: <ArrowRightLeft className="size-3.5 text-zinc-400" />,
    ring: "bg-white/[0.06] ring-white/15",
    label: "State change",
  },
};

function summarize(step: Step): string {
  if (step.type === "llm_call") {
    const model = step.input?.model;
    return typeof model === "string" ? model : "";
  }
  if (step.type === "tool_call") {
    const name = step.input?.name;
    return typeof name === "string" ? `${name}()` : "";
  }
  const from = step.input?.from_state;
  const to = step.input?.to_state;
  return typeof from === "string" && typeof to === "string"
    ? `${from} → ${to}`
    : "";
}

function JsonBlock({ label, value }: { label: string; value: unknown }) {
  return (
    <div>
      <div className="text-[10px] font-semibold uppercase tracking-widest text-zinc-500">
        {label}
      </div>
      <pre className="mt-1.5 max-h-96 overflow-auto rounded-lg border border-white/[0.06] bg-black/40 p-3 font-mono text-xs leading-relaxed text-zinc-300">
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
  const { icon, ring, label } = TYPE_CONFIG[step.type];
  const summary = summarize(step);

  return (
    <div
      id={`step-${step.seq}`}
      className="rounded-xl border border-white/[0.07] bg-white/[0.03] backdrop-blur-xl transition-colors hover:border-white/[0.14]"
    >
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        aria-expanded={expanded}
        className="flex w-full cursor-pointer items-center gap-3 px-4 py-3 text-left"
      >
        <span
          className={cn(
            "flex size-7 shrink-0 items-center justify-center rounded-lg ring-1",
            ring,
          )}
        >
          {icon}
        </span>

        <span className="min-w-0 flex-1">
          <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <span className="text-sm font-medium text-zinc-100">{label}</span>
            {summary && (
              <span className="truncate font-mono text-xs text-zinc-500">
                {summary}
              </span>
            )}
            {parentOrigin && <Badge variant="outline">parent</Badge>}
          </span>
        </span>

        <span className="flex shrink-0 items-center gap-3 text-[11px] text-zinc-500">
          {step.latency_ms != null && (
            <span className="hidden items-center gap-1 sm:flex">
              <Clock className="size-3" />
              {step.latency_ms}ms
            </span>
          )}
          {step.tokens_in != null && step.tokens_out != null && (
            <span className="hidden items-center gap-1 sm:flex">
              <Coins className="size-3" />
              {step.tokens_in}→{step.tokens_out}
            </span>
          )}
          <span className="font-mono text-zinc-600">#{step.seq}</span>
          <ChevronDown
            className={cn(
              "size-4 text-zinc-600 transition-transform duration-200",
              expanded && "rotate-180",
            )}
          />
        </span>
      </button>

      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="space-y-3 border-t border-white/[0.06] px-4 py-3">
              <JsonBlock label="input · verbatim" value={step.input} />
              <JsonBlock label="output · verbatim" value={step.output} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
