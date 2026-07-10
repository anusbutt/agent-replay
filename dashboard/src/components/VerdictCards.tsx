import { Lightbulb, Microscope, MoveRight, Radar } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { VerdictPassFailBadge } from "@/components/VerdictBadge";
import type { AnalysisVerdict, DetectionVerdict } from "@/lib/api";

export function DetectionCard({ detection }: { detection: DetectionVerdict }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <Radar className="size-4 text-zinc-400" />
          Detection
          <VerdictPassFailBadge verdict={detection.verdict} />
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-3">
        <p className="text-sm leading-relaxed text-zinc-300">
          {detection.reason}
        </p>
        {detection.contradiction && (
          <div className="mt-3 flex flex-col gap-2 rounded-xl border border-white/[0.06] bg-black/25 p-3 text-xs sm:flex-row sm:items-center">
            <div className="flex-1">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-600">
                User intent
              </p>
              <p className="mt-1 italic text-zinc-300">
                “{detection.contradiction.user_intent}”
              </p>
            </div>
            <MoveRight className="hidden size-4 shrink-0 text-red-400/60 sm:block" />
            <div className="flex-1">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-600">
                Agent action
              </p>
              <p className="mt-1 italic text-red-300">
                “{detection.contradiction.agent_action}”
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function AnalysisCard({ analysis }: { analysis: AnalysisVerdict }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <Microscope className="size-4 text-zinc-400" />
          Root cause
          <a href={`#step-${analysis.failing_step}`}>
            <Badge variant="violet" className="cursor-pointer hover:bg-violet-500/20">
              failing step {analysis.failing_step}
            </Badge>
          </a>
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-3">
        <p className="text-sm leading-relaxed text-zinc-300">
          {analysis.root_cause}
        </p>
        <div className="mt-3 flex items-start gap-2.5 rounded-xl border border-emerald-400/20 bg-emerald-500/[0.06] p-3">
          <Lightbulb className="mt-0.5 size-4 shrink-0 text-emerald-300" />
          <div className="text-sm leading-relaxed text-emerald-100">
            <span className="font-medium">Suggested fix — </span>
            {analysis.suggested_fix}
            <a
              href="#fork"
              className="mt-1.5 block text-xs font-medium text-emerald-300 underline-offset-2 hover:underline"
            >
              Apply it in a fork ↓
            </a>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
