import { Skeleton } from "@/components/ui/skeleton";

export default function Loading() {
  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <Skeleton className="h-8 w-32" />
      <Skeleton className="mt-2 h-4 w-48" />
      <div className="mt-6 flex flex-col gap-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-[70px] rounded-2xl" />
        ))}
      </div>
    </div>
  );
}
