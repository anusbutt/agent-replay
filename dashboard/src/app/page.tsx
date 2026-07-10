import { listRuns } from "@/lib/api";
import { RunsList } from "@/components/RunsList";

export default async function RunsListPage() {
  const runs = await listRuns({ limit: 100 });
  const flagged = runs.filter((r) => r.status === "flagged").length;
  const forks = runs.filter((r) => r.parent_run_id != null).length;

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-50">
            Runs
          </h1>
          <p className="mt-1 text-sm text-zinc-500">
            {runs.length} recorded
            {flagged > 0 && ` · ${flagged} flagged`}
            {forks > 0 && ` · ${forks} fork${forks === 1 ? "" : "s"}`}
          </p>
        </div>
      </div>

      <div className="mt-6">
        <RunsList runs={runs} />
      </div>
    </div>
  );
}
