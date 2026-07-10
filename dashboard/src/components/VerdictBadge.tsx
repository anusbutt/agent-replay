import {
  CircleCheck,
  CircleDot,
  CircleX,
  Flag,
  ShieldCheck,
  ShieldAlert,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { RunStatus } from "@/lib/api";

const STATUS_CONFIG: Record<
  RunStatus,
  { variant: "sky" | "default" | "red" | "amber"; icon: React.ReactNode }
> = {
  running: { variant: "sky", icon: <CircleDot className="animate-pulse" /> },
  completed: { variant: "default", icon: <CircleCheck /> },
  failed: { variant: "red", icon: <CircleX /> },
  flagged: { variant: "amber", icon: <Flag /> },
};

export function StatusBadge({ status }: { status: RunStatus }) {
  const { variant, icon } = STATUS_CONFIG[status];
  return (
    <Badge variant={variant}>
      {icon}
      {status}
    </Badge>
  );
}

export function VerdictPassFailBadge({
  verdict,
}: {
  verdict: "pass" | "fail";
}) {
  return verdict === "fail" ? (
    <Badge variant="red">
      <ShieldAlert />
      fail
    </Badge>
  ) : (
    <Badge variant="emerald">
      <ShieldCheck />
      pass
    </Badge>
  );
}
