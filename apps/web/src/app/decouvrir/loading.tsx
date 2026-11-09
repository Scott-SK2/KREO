import { SkeletonCard } from "@/components/ui/Skeleton";

export default function Loading() {
  return (
    <div className="kreo-container py-10">
      <div className="h-9 w-48 animate-pulse rounded-md bg-ivory" />
      <div className="mt-8 h-11 w-full animate-pulse rounded-md bg-ivory" />
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
    </div>
  );
}
