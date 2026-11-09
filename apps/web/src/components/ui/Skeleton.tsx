import { cn } from "@/lib/cn";

/** Bloc de chargement animé ; purement décoratif (aria-hidden). */
export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden="true" className={cn("animate-pulse rounded-md bg-ivory", className)} />;
}

/** Carte fantôme pour les listes d'annonces et de projets. */
export function SkeletonCard() {
  return (
    <div className="rounded-xl border border-taupe/15 bg-white p-5">
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="mt-3 h-6 w-3/4" />
      <Skeleton className="mt-4 h-4 w-full" />
      <Skeleton className="mt-2 h-4 w-5/6" />
      <div className="mt-5 flex gap-2">
        <Skeleton className="h-6 w-20 rounded-full" />
        <Skeleton className="h-6 w-24 rounded-full" />
      </div>
    </div>
  );
}
