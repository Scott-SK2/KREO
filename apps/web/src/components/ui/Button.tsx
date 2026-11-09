import Link from "next/link";
import type { ComponentPropsWithoutRef, ReactNode } from "react";

import { cn } from "@/lib/cn";

import { Spinner } from "./Spinner";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "sm" | "md" | "lg";

const base =
  "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors duration-200 ease-kreo select-none disabled:cursor-not-allowed disabled:opacity-60 min-h-touch";

const variants: Record<ButtonVariant, string> = {
  primary: "bg-taupe text-white hover:bg-taupe-dark active:bg-brown",
  secondary:
    "border border-taupe text-taupe-dark bg-transparent hover:bg-ivory active:bg-ivory/80",
  ghost: "text-taupe-dark hover:bg-ivory active:bg-ivory/80",
  danger: "bg-bordeaux text-white hover:bg-bordeaux/90 active:bg-bordeaux/80",
};

const sizes: Record<ButtonSize, string> = {
  sm: "px-3 text-sm",
  md: "px-4 py-2 text-sm sm:text-base",
  lg: "px-6 py-3 text-base",
};

/** Classes d'un bouton KREO, réutilisables sur un lien stylé en bouton. */
export function buttonClasses(
  variant: ButtonVariant = "primary",
  size: ButtonSize = "md",
  className?: string,
) {
  return cn(base, variants[variant], sizes[size], className);
}

export interface ButtonProps extends ComponentPropsWithoutRef<"button"> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  /** Affiche un indicateur et désactive le bouton. */
  loading?: boolean;
  /** Icône (lucide) affichée avant le libellé. */
  icon?: ReactNode;
}

/**
 * Bouton accessible (cible ≥ 44 px, focus visible, état de chargement annoncé).
 */
export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  icon,
  className,
  children,
  disabled,
  type = "button",
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      className={buttonClasses(variant, size, className)}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading ? <Spinner className="size-4" /> : icon}
      {children}
    </button>
  );
}

export interface ButtonLinkProps extends ComponentPropsWithoutRef<typeof Link> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: ReactNode;
}

/** Lien Next.js habillé en bouton (navigation, pas d'action). */
export function ButtonLink({
  variant = "primary",
  size = "md",
  icon,
  className,
  children,
  ...rest
}: ButtonLinkProps) {
  return (
    <Link className={buttonClasses(variant, size, className)} {...rest}>
      {icon}
      {children}
    </Link>
  );
}
