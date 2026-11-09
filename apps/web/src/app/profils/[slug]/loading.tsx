import { Skeleton, SkeletonCard } from "@/components/ui/Skeleton";

export default function Loading() {
  return (
    <div className="kreo-container py-10" aria-busy="true">
      <Skeleton className="h-4 w-40" />
      <Skeleton className="mt-3 h-10 w-2/3" />
      <div className="mt-10 grid gap-6 lg:grid-cols-[1fr_20rem]">
        <div className="flex flex-col gap-4">
          <Skeleton className="h-24 w-full" />
          <SkeletonCard />
          <SkeletonCard />
        </div>
        <Skeleton className="h-48 w-full" />
      </div>
    </div>
  );
}
