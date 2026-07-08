import type { RunDetail, Step } from "@/lib/api";
import { TimelineStep } from "@/components/TimelineStep";

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
    (s) => fork.fork_step != null && s.seq > fork.fork_step && s.type === "tool_call",
  );

  return (
    <div className="rounded-lg border border-violet-200 bg-violet-50/50 p-5 dark:border-violet-900 dark:bg-violet-950/20">
      <h3 className="text-sm font-semibold text-violet-900 dark:text-violet-300">
        Compare — original vs. fork (step {fork.fork_step})
      </h3>
      <p className="mt-1 text-xs text-violet-700 dark:text-violet-400">
        The fork replays the exact recorded context at step {fork.fork_step}{" "}
        with the fix applied, at temperature 0. No tool was invoked and no
        real booking occurred.
      </p>

      <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <span className="rounded bg-zinc-200 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
              parent-origin
            </span>
            <span className="text-xs font-semibold text-zinc-500">
              Original — step {fork.fork_step}
            </span>
          </div>
          <div className="rounded border border-zinc-200 bg-white p-3 text-sm text-zinc-800 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-200">
            {assistantText(parentStepK)}
          </div>
          {parentSubsequentToolCalls.length > 0 && (
            <div className="mt-3 space-y-2">
              {parentSubsequentToolCalls.map((s) => (
                <TimelineStep key={s.id} step={s} parentOrigin />
              ))}
            </div>
          )}
        </div>

        <div>
          <div className="mb-2 flex items-center gap-2">
            <span className="rounded bg-emerald-200 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300">
              fork
            </span>
            <span className="text-xs font-semibold text-zinc-500">
              Fork {fork.id.slice(0, 8)}… — step 1
            </span>
          </div>
          <div className="rounded border border-emerald-300 bg-emerald-50 p-3 text-sm text-emerald-900 dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200">
            {assistantText(forkStep)}
          </div>
          <p className="mt-3 text-xs text-zinc-500">
            No tool call — the fork never re-books anything.
          </p>
        </div>
      </div>
    </div>
  );
}
