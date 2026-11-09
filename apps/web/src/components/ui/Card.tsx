import type { ComponentPropsWithoutRef, ElementType } from "react";

import { cn } from "@/lib/cn";

export interface CardProps extends ComponentPropsWithoutRef<"div"> {
  /** Balise rendue (article, section, li…). */
  as?: ElementType;
  /** Surélévation au survol pour les cartes cliquables. */
  interactive?: boolean;
  padding?: "none" | "sm" | "md" | "lg";
}

const paddings = { none: "", sm: "p-4", md: "p-5 sm:p-6", lg: "p-6 sm:p-8" };

/** Surface blanche à bord doux : brique de base des listes et panneaux. */
export function Card({
  as: Tag = "div",
  interactive = false,
  padding = "md",
  className,
  ...rest
}: CardProps) {
  return (
    <Tag
      className={cn(
        "rounded-xl border border-taupe/15 bg-white shadow-sm",
        interactive &&
          "transition-shadow duration-200 ease-kreo hover:shadow-md focus-within:ring-2 focus-within:ring-focus",
        paddings[padding],
        className,
      )}
      {...rest}
    />
  );
}
