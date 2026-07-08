import type { RunStatus } from "@/lib/api";

const STATUS_STYLES: Record<RunStatus, string> = {
  running: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300",
  completed:
    "bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-300",
  failed: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
  flagged:
    "bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-300",
};

export function StatusBadge({ status }: { status: RunStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLES[status]}`}
    >
      {status}
    </span>
  );
}

export function VerdictPassFailBadge({ verdict }: { verdict: "pass" | "fail" }) {
  const style =
    verdict === "fail"
      ? "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300"
      : "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${style}`}
    >
      {verdict}
    </span>
  );
}
