import { cn } from "@/lib/cn";

/** Indicateur d'activité discret (anneau tournant), décoratif. */
export function Spinner({ className }: { className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        "inline-block animate-spin rounded-full border-2 border-current border-r-transparent",
        className ?? "size-5",
      )}
    />
  );
}
