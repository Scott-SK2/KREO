import { cn } from "@/lib/cn";

export interface RingsPatternProps {
  className?: string;
  /** Nombre de cercles concentriques. */
  rings?: number;
  /** Couleur de trait (variable CSS ou couleur). */
  stroke?: string;
}

/**
 * Motif KREO : fins cercles concentriques (ondes) pour couvertures et héros.
 * Décoratif, masqué aux technologies d'assistance.
 */
export function RingsPattern({
  className,
  rings = 9,
  stroke = "var(--kreo-color-taupe)",
}: RingsPatternProps) {
  const step = 50 / (rings + 0.5);
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      viewBox="0 0 100 100"
      className={cn("pointer-events-none text-taupe", className)}
    >
      {Array.from({ length: rings }, (_, i) => (
        <circle
          key={i}
          cx="50"
          cy="50"
          r={step * (i + 1)}
          fill="none"
          stroke={stroke}
          strokeOpacity={0.18 + (i % 3 === 0 ? 0.06 : 0)}
          strokeWidth={0.6}
          vectorEffect="non-scaling-stroke"
        />
      ))}
    </svg>
  );
}
