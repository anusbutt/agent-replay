import { GitFork, ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { TimelineStep } from "@/components/TimelineStep";
import { shortId } from "@/lib/format";
import type { RunDetail, Step } from "@/lib/api";

function assistantText(step: Step | undefined): string {
  if (!step) return "(no reply recorded)";
  const choices = step.output?.choices as
    | { message?: { content?: string } }[]
    | undefined;
  return choices?.[0]?.message?.content ?? "(no reply recorded)";
}

/**
 * Side-by-side proof of the flipped decision (research R4 single-shot):
 * the fork's assistant text against the parent's step-K text AND the
 * parent's subsequent tool_call step(s), parent steps clearly labeled
 * parent-origin.
 */
export function CompareView({
  parent,
  fork,
}: {
  parent: RunDetail;
  fork: RunDetail;
}) {
  const forkStep = fork.steps.find((s) => s.seq === 1);
  const parentStepK = parent.steps.find((s) => s.seq === fork.fork_step);
  const parentSubsequentToolCalls = parent.steps.filter(
    (s) =>
      fork.fork_step != null &&
      s.seq > fork.fork_step &&
      s.type === "tool_call",
  );

  return (
    <Card className="border-violet-400/20 bg-violet-500/[0.04]">
      <CardHeader>
        <CardTitle>
          <GitFork className="size-4 text-violet-300" />
          Original vs. fork — step {fork.fork_step}
        </CardTitle>
        <CardDescription>
          Same recorded context, fix applied, temperature 0. The only variable
          is your modification.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <div className="mb-2 flex items-center gap-2">
              <Badge variant="outline">parent-origin</Badge>
              <span className="text-xs font-medium text-zinc-500">
                Original · step {fork.fork_step}
              </span>
            </div>
            <div className="rounded-xl border border-white/[0.08] bg-black/30 p-4 text-sm leading-relaxed text-zinc-300">
              {assistantText(parentStepK)}
            </div>
            {parentSubsequentToolCalls.length > 0 && (
              <div className="mt-3 space-y-2">
                <p className="text-[11px] font-medium uppercase tracking-widest text-zinc-600">
                  What originally happened next
                </p>
                {parentSubsequentToolCalls.map((s) => (
                  <TimelineStep key={s.id} step={s} parentOrigin />
                ))}
              </div>
            )}
          </div>

          <div>
            <div className="mb-2 flex items-center gap-2">
              <Badge variant="emerald">
                <GitFork />
                fork
              </Badge>
              <span className="text-xs font-medium text-zinc-500">
                {shortId(fork.id)} · step 1
              </span>
            </div>
            <div className="rounded-xl border border-emerald-400/25 bg-emerald-500/[0.07] p-4 text-sm leading-relaxed text-emerald-100 shadow-[0_0_32px_-12px_rgba(52,211,153,0.25)]">
              {assistantText(forkStep)}
            </div>
            <p className="mt-3 flex items-center gap-1.5 text-xs text-zinc-500">
              <ShieldCheck className="size-3.5 text-emerald-400/70" />
              No tool call issued — the fork never re-books anything.
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
