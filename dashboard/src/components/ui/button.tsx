import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-200 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 outline-none focus-visible:ring-2 focus-visible:ring-violet-400/40 cursor-pointer",
  {
    variants: {
      variant: {
        default:
          "bg-violet-500 text-white shadow-[0_0_20px_-4px_rgba(139,92,246,0.5)] hover:bg-violet-400 hover:shadow-[0_0_28px_-4px_rgba(139,92,246,0.65)] active:scale-[0.98]",
        glass:
          "border border-white/10 bg-white/[0.04] text-zinc-200 backdrop-blur-md hover:bg-white/[0.09] hover:border-white/20 active:scale-[0.98]",
        ghost:
          "text-zinc-400 hover:text-zinc-100 hover:bg-white/[0.06] active:scale-[0.98]",
        destructive:
          "border border-red-500/30 bg-red-500/10 text-red-300 hover:bg-red-500/20 active:scale-[0.98]",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-lg px-6",
        icon: "size-8 rounded-md",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

function Button({
  className,
  variant,
  size,
  ...props
}: React.ComponentProps<"button"> & VariantProps<typeof buttonVariants>) {
  return (
    <button
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  );
}

export { Button, buttonVariants };
