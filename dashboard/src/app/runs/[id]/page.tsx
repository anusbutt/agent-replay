import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, GitFork, Timer } from "lucide-react";
import { getRun, ApiRequestError } from "@/lib/api";
import { StatusBadge } from "@/components/VerdictBadge";
import { Badge } from "@/components/ui/badge";
import { TimelineStep } from "@/components/TimelineStep";
import { RunActions } from "@/components/RunActions";
import { ForkPanel } from "@/components/ForkPanel";
import { CompareView } from "@/components/CompareView";
import { CopyButton } from "@/components/CopyButton";
import { AnalysisCard, DetectionCard } from "@/components/VerdictCards";
import { formatDateTime, formatDuration, shortId } from "@/lib/format";

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
    <div className="mx-auto max-w-4xl px-6 py-8">
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-xs font-medium text-zinc-500 transition-colors hover:text-zinc-200"
      >
        <ArrowLeft className="size-3.5" />
        All runs
      </Link>

      {/* Header */}
      <div className="mt-4 flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-xl font-bold tracking-tight text-zinc-50">
            {run.agent_id}
            <span className="mx-2 text-zinc-600">/</span>
            <span className="font-medium text-zinc-400">{run.session_id}</span>
          </h1>
          <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-zinc-500">
            <span className="inline-flex items-center gap-1.5 font-mono">
              {shortId(run.id)}
              <CopyButton text={run.id} />
            </span>
            <span>{formatDateTime(run.started_at)}</span>
            <span className="inline-flex items-center gap-1">
              <Timer className="size-3" />
              {formatDuration(run.started_at, run.ended_at)}
            </span>
          </div>
        </div>
        <StatusBadge status={run.status} />
      </div>

      {run.parent_run_id && (
        <Link href={`/runs/${run.parent_run_id}`} className="mt-3 inline-block">
          <Badge variant="violet" className="cursor-pointer py-1 hover:bg-violet-500/20">
            <GitFork />
            Forked from {shortId(run.parent_run_id)} at step {run.fork_step} —
            view original
          </Badge>
        </Link>
      )}

      {!run.parent_run_id && (
        <div className="mt-5">
          <RunActions runId={run.id} status={run.status} />
        </div>
      )}

      {/* Verdicts */}
      {(detection || analysis) && (
        <div className="mt-5 space-y-3">
          {detection && <DetectionCard detection={detection} />}
          {analysis && <AnalysisCard analysis={analysis} />}
        </div>
      )}

      {/* Fork comparison (forks only) */}
      {parent && (
        <div className="mt-5">
          <CompareView parent={parent} fork={run} />
        </div>
      )}

      {/* Fork form (original runs only) */}
      {!run.parent_run_id && (
        <div className="mt-5">
          <ForkPanel run={run} />
        </div>
      )}

      {/* Timeline */}
      <h2 className="mt-8 text-[11px] font-semibold uppercase tracking-widest text-zinc-500">
        Timeline — {run.steps.length} step{run.steps.length === 1 ? "" : "s"}
      </h2>
      <div className="mt-3 space-y-2">
        {run.steps.map((step) => (
          <TimelineStep key={step.id} step={step} />
        ))}
        {run.steps.length === 0 && (
          <p className="text-sm text-zinc-500">No steps recorded.</p>
        )}
      </div>
    </div>
  );
}
