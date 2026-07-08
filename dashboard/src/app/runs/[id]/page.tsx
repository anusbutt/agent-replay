import Link from "next/link";
import { notFound } from "next/navigation";
import { getRun, ApiRequestError } from "@/lib/api";
import { StatusBadge, VerdictPassFailBadge } from "@/components/VerdictBadge";
import { TimelineStep } from "@/components/TimelineStep";
import { RunActions } from "@/components/RunActions";
import { ForkPanel } from "@/components/ForkPanel";
import { CompareView } from "@/components/CompareView";

export default async function RunDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let run;
  try {
    run = await getRun(id);
  } catch (err) {
    if (err instanceof ApiRequestError && err.status === 404) notFound();
    throw err;
  }

  const parent = run.parent_run_id ? await getRun(run.parent_run_id) : null;
  const { detection, analysis } = run.run_metadata;

  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      <Link
        href="/"
        className="text-xs font-medium text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200"
      >
        ← all runs
      </Link>

      <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-zinc-900 dark:text-zinc-50">
            {run.agent_id} — {run.session_id}
          </h1>
          <p className="mt-1 font-mono text-xs text-zinc-400">{run.id}</p>
        </div>
        <StatusBadge status={run.status} />
      </div>

      {run.parent_run_id && (
        <p className="mt-2 text-xs text-zinc-500">
          🔀 forked from{" "}
          <Link
            href={`/runs/${run.parent_run_id}`}
            className="text-violet-700 hover:underline dark:text-violet-400"
          >
            {run.parent_run_id.slice(0, 8)}…
          </Link>{" "}
          at step {run.fork_step}
        </p>
      )}

      <div className="mt-6">
        <RunActions runId={run.id} />
      </div>

      {(detection || analysis) && (
        <div className="mt-6 space-y-3">
          {detection && (
            <div className="rounded border border-zinc-200 p-4 dark:border-zinc-800">
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                  Detection
                </span>
                <VerdictPassFailBadge verdict={detection.verdict} />
              </div>
              <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
                {detection.reason}
              </p>
              {detection.contradiction && (
                <p className="mt-1 text-xs text-zinc-500">
                  user intent: <em>{detection.contradiction.user_intent}</em>{" "}
                  — agent action:{" "}
                  <em>{detection.contradiction.agent_action}</em>
                </p>
              )}
            </div>
          )}
          {analysis && (
            <div className="rounded border border-zinc-200 p-4 dark:border-zinc-800">
              <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                Analysis — failing step {analysis.failing_step}
              </span>
              <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
                {analysis.root_cause}
              </p>
              <p className="mt-1 text-sm text-emerald-700 dark:text-emerald-400">
                Suggested fix: {analysis.suggested_fix}
              </p>
            </div>
          )}
        </div>
      )}

      {parent && (
        <div className="mt-6">
          <CompareView parent={parent} fork={run} />
        </div>
      )}

      {!run.parent_run_id && (
        <div className="mt-6">
          <ForkPanel run={run} />
        </div>
      )}

      <h2 className="mt-8 text-sm font-semibold uppercase tracking-wide text-zinc-500">
        Timeline
      </h2>
      <div className="mt-3 space-y-2">
        {run.steps.map((step) => (
          <TimelineStep key={step.id} step={step} />
        ))}
        {run.steps.length === 0 && (
          <p className="text-sm text-zinc-400">No steps recorded.</p>
        )}
      </div>
    </div>
  );
}
