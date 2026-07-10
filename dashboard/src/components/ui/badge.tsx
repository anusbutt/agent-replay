import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-medium tracking-wide transition-colors [&_svg]:size-3",
  {
    variants: {
      variant: {
        default: "border-white/10 bg-white/[0.06] text-zinc-300",
        violet: "border-violet-400/25 bg-violet-500/10 text-violet-300",
        emerald: "border-emerald-400/25 bg-emerald-500/10 text-emerald-300",
        red: "border-red-400/25 bg-red-500/10 text-red-300",
        amber: "border-amber-400/25 bg-amber-500/10 text-amber-300",
        sky: "border-sky-400/25 bg-sky-500/10 text-sky-300",
        outline: "border-white/15 bg-transparent text-zinc-400",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

function Badge({
  className,
  variant,
  ...props
}: React.ComponentProps<"span"> & VariantProps<typeof badgeVariants>) {
  return (
    <span
      data-slot="badge"
      className={cn(badgeVariants({ variant }), className)}
      {...props}
    />
  );
}

export { Badge, badgeVariants };
