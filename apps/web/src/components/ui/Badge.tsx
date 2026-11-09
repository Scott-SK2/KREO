import type { ComponentPropsWithoutRef } from "react";

import { cn } from "@/lib/cn";

export type BadgeTone = "neutral" | "gold" | "success" | "warning" | "bordeaux" | "ink";

const tones: Record<BadgeTone, string> = {
  neutral: "bg-ivory text-taupe-dark",
  gold: "bg-gold/20 text-brown",
  success: "bg-success/15 text-success",
  warning: "bg-warning/15 text-warning",
  bordeaux: "bg-bordeaux/10 text-bordeaux",
  ink: "bg-ink text-paper",
};

export interface BadgeProps extends ComponentPropsWithoutRef<"span"> {
  tone?: BadgeTone;
}

/** Pastille de texte courte (statut, rémunération, mention). */
export function Badge({ tone = "neutral", className, ...rest }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium whitespace-nowrap",
        tones[tone],
        className,
      )}
      {...rest}
    />
  );
}

export type CompensationType = "paid" | "volunteer" | "expenses" | "negotiable";

/** Teinte de pastille par type de rémunération. */
export const compensationTone: Record<CompensationType, BadgeTone> = {
  paid: "gold",
  volunteer: "neutral",
  expenses: "success",
  negotiable: "warning",
};

export interface CompensationBadgeProps extends Omit<BadgeProps, "tone"> {
  compensation: CompensationType;
  /** Libellé traduit (ex. t(`compensation.${compensation}`)). */
  label: string;
}

/** Pastille de rémunération : chaque rôle affiche la sienne, sans exception. */
export function CompensationBadge({ compensation, label, ...rest }: CompensationBadgeProps) {
  return (
    <Badge tone={compensationTone[compensation]} data-compensation={compensation} {...rest}>
      {label}
    </Badge>
  );
}

/** Teintes des statuts de candidature et de projet. */
export const statusTone: Record<string, BadgeTone> = {
  submitted: "neutral",
  viewed: "neutral",
  shortlisted: "gold",
  audition: "gold",
  offered: "gold",
  accepted: "success",
  declined: "bordeaux",
  rejected: "bordeaux",
  withdrawn: "neutral",
  draft: "neutral",
  preparing: "warning",
  active: "success",
  completed: "ink",
  cancelled: "bordeaux",
  archived: "neutral",
  open: "success",
  filled: "ink",
  closed: "neutral",
  confirmed: "gold",
  proposed: "warning",
  disputed: "bordeaux",
};

export interface StatusBadgeProps extends Omit<BadgeProps, "tone"> {
  status: string;
  label: string;
}

/** Pastille de statut avec teinte dérivée du statut métier. */
export function StatusBadge({ status, label, ...rest }: StatusBadgeProps) {
  return (
    <Badge tone={statusTone[status] ?? "neutral"} data-status={status} {...rest}>
      {label}
    </Badge>
  );
}
