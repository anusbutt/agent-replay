"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Bot, ChevronRight, GitFork, Inbox, MessageSquare } from "lucide-react";
import { StatusBadge } from "@/components/VerdictBadge";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { formatRelative, shortId } from "@/lib/format";
import type { Run } from "@/lib/api";

const listVariants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.04 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 8 },
  show: { opacity: 1, y: 0, transition: { duration: 0.25, ease: "easeOut" as const } },
};

export function RunsList({ runs }: { runs: Run[] }) {
  if (runs.length === 0) {
    return (
      <Card className="flex flex-col items-center gap-3 px-6 py-14 text-center">
        <span className="flex size-12 items-center justify-center rounded-2xl bg-white/[0.04] ring-1 ring-white/10">
          <Inbox className="size-5 text-zinc-500" />
        </span>
        <p className="text-sm font-medium text-zinc-300">No runs recorded yet</p>
        <p className="max-w-sm text-xs leading-relaxed text-zinc-500">
          Seed the demo run (<code className="font-mono">python scripts/seed_demo_run.py</code>)
          or instrument an agent with the SDK — every LLM call, tool call, and
          state change lands here automatically.
        </p>
      </Card>
    );
  }

  return (
    <motion.ul
      variants={listVariants}
      initial="hidden"
      animate="show"
      className="flex flex-col gap-2"
    >
      {runs.map((run) => (
        <motion.li key={run.id} variants={itemVariants}>
          <Link href={`/runs/${run.id}`} className="group block">
            <Card className="flex items-center gap-4 px-5 py-3.5 transition-all duration-200 group-hover:border-white/[0.16] group-hover:bg-white/[0.05]">
              <span className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-white/[0.04] ring-1 ring-white/10">
                <Bot className="size-4 text-zinc-400" />
              </span>

              <span className="min-w-0 flex-1">
                <span className="flex items-center gap-2">
                  <span className="truncate text-sm font-semibold text-zinc-100">
                    {run.agent_id}
                  </span>
                  {run.parent_run_id && (
                    <Badge variant="violet">
                      <GitFork />
                      fork of {shortId(run.parent_run_id)}
                      {run.fork_step != null && ` @ step ${run.fork_step}`}
                    </Badge>
                  )}
                </span>
                <span className="mt-0.5 flex items-center gap-1.5 text-xs text-zinc-500">
                  <MessageSquare className="size-3" />
                  <span className="truncate">{run.session_id}</span>
                </span>
              </span>

              <span className="hidden shrink-0 sm:block">
                <StatusBadge status={run.status} />
              </span>

              <span className="hidden w-20 shrink-0 text-right text-xs text-zinc-500 md:block">
                {formatRelative(run.started_at)}
              </span>

              <ChevronRight className="size-4 shrink-0 text-zinc-600 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:text-zinc-300" />
            </Card>
          </Link>
        </motion.li>
      ))}
    </motion.ul>
  );
}
