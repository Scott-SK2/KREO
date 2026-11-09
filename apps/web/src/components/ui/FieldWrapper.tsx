import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

export interface FieldWrapperProps {
  id: string;
  label: ReactNode;
  hint?: ReactNode;
  error?: ReactNode;
  optional?: string;
  className?: string;
  children: ReactNode;
}

/** Ids des descriptions (indice, erreur) à relier via aria-describedby. */
export function describedBy(id: string, hint?: unknown, error?: unknown) {
  const ids = [hint ? `${id}-hint` : null, error ? `${id}-error` : null].filter(Boolean);
  return ids.length ? ids.join(" ") : undefined;
}

/** Étiquette + indice + erreur partagés par les champs de formulaire. */
export function FieldWrapper({
  id,
  label,
  hint,
  error,
  optional,
  className,
  children,
}: FieldWrapperProps) {
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <label htmlFor={id} className="text-sm font-medium text-brown">
        {label}
        {optional ? <span className="ml-1 font-normal text-taupe">({optional})</span> : null}
      </label>
      {children}
      {hint ? (
        <p id={`${id}-hint`} className="text-sm text-taupe-dark">
          {hint}
        </p>
      ) : null}
      {error ? (
        <p id={`${id}-error`} role="alert" className="text-sm font-medium text-bordeaux">
          {error}
        </p>
      ) : null}
    </div>
  );
}

export const controlClasses =
  "w-full min-h-touch rounded-md border bg-white px-3 py-2 text-base text-ink placeholder:text-taupe/70 transition-colors focus-visible:ring-2 focus-visible:ring-focus focus-visible:ring-offset-2 focus-visible:ring-offset-paper focus-visible:outline-none disabled:bg-ivory disabled:text-taupe-dark";

export function controlBorder(error?: unknown) {
  return error ? "border-bordeaux" : "border-taupe/40 hover:border-taupe";
}
