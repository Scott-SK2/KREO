import { cn } from "@/lib/cn";

export interface LogoProps {
  className?: string;
  /** Hauteur en pixels ; la largeur suit le ratio. */
  height?: number;
  /** Variante claire pour les fonds sombres. */
  inverted?: boolean;
}

/**
 * Wordmark KREO : lettres capitales en Playfair Display 900, le O dessiné
 * comme deux anneaux qui se chevauchent (trait fin, accent or).
 */
export function Logo({ className, height = 28, inverted = false }: LogoProps) {
  const color = inverted ? "var(--kreo-color-paper)" : "var(--kreo-color-brown)";
  return (
    <svg
      role="img"
      aria-label="KREO"
      viewBox="0 0 150 40"
      height={height}
      width={(150 / 40) * height}
      className={cn("shrink-0", className)}
    >
      <text
        x="0"
        y="32"
        fontFamily="var(--font-playfair), 'Playfair Display', Georgia, serif"
        fontWeight="900"
        fontSize="36"
        letterSpacing="1.5"
        fill={color}
      >
        KRE
      </text>
      <g fill="none" strokeWidth="2.6">
        <circle cx="117" cy="21" r="13" stroke={color} />
        <circle cx="129" cy="21" r="13" stroke="var(--kreo-color-gold)" />
      </g>
    </svg>
  );
}
