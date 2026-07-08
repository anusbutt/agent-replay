import Link from "next/link";
import { listRuns } from "@/lib/api";
import { StatusBadge } from "@/components/VerdictBadge";

export default async function RunsListPage() {
  const runs = await listRuns({ limit: 100 });

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">
        AgentReplay — Runs
      </h1>
      <p className="mt-1 text-sm text-zinc-500">
        {runs.length} run{runs.length === 1 ? "" : "s"} recorded
      </p>

      <div className="mt-6 overflow-hidden rounded-lg border border-zinc-200 dark:border-zinc-800">
        <table className="min-w-full divide-y divide-zinc-200 dark:divide-zinc-800">
          <thead className="bg-zinc-50 dark:bg-zinc-900">
            <tr>
              <Th>Agent</Th>
              <Th>Session</Th>
              <Th>Status</Th>
              <Th>Lineage</Th>
              <Th>Started</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-200 bg-white dark:divide-zinc-800 dark:bg-zinc-950">
            {runs.map((run) => (
              <tr
                key={run.id}
                className="hover:bg-zinc-50 dark:hover:bg-zinc-900"
              >
                <td className="px-4 py-3">
                  <Link
                    href={`/runs/${run.id}`}
                    className="font-medium text-violet-700 hover:underline dark:text-violet-400"
                  >
                    {run.agent_id}
                  </Link>
                </td>
                <td className="px-4 py-3 text-sm text-zinc-600 dark:text-zinc-400">
                  {run.session_id}
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={run.status} />
                </td>
                <td className="px-4 py-3 text-sm text-zinc-500">
                  {run.parent_run_id ? (
                    <span title={`forked from ${run.parent_run_id} at step ${run.fork_step}`}>
                      🔀 fork of {run.parent_run_id.slice(0, 8)}…
                    </span>
                  ) : (
                    <span className="text-zinc-300 dark:text-zinc-700">—</span>
                  )}
                </td>
                <td className="px-4 py-3 text-sm text-zinc-500">
                  {run.started_at
                    ? new Date(run.started_at).toLocaleString()
                    : "—"}
                </td>
              </tr>
            ))}
            {runs.length === 0 && (
              <tr>
                <td
                  colSpan={5}
                  className="px-4 py-10 text-center text-sm text-zinc-400"
                >
                  No runs yet. Seed the demo run or instrument an agent with
                  the SDK.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500">
      {children}
    </th>
  );
}
