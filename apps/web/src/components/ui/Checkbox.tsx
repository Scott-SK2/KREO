import type { ComponentPropsWithoutRef, ReactNode } from "react";

import { cn } from "@/lib/cn";

export interface CheckboxProps extends Omit<ComponentPropsWithoutRef<"input">, "id" | "type"> {
  id: string;
  label: ReactNode;
  hint?: ReactNode;
  error?: ReactNode;
}

/** Case à cocher native, zone cliquable ≥ 44 px sur toute la ligne. */
export function Checkbox({ id, label, hint, error, className, ...rest }: CheckboxProps) {
  const describedBy =
    [hint ? `${id}-hint` : null, error ? `${id}-error` : null].filter(Boolean).join(" ") ||
    undefined;
  return (
    <div className={cn("flex flex-col gap-1", className)}>
      <label
        htmlFor={id}
        className="flex min-h-touch cursor-pointer items-start gap-3 py-2 text-base text-brown"
      >
        <input
          id={id}
          type="checkbox"
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          className="mt-1 size-5 shrink-0 cursor-pointer rounded-sm border-taupe accent-taupe"
          {...rest}
        />
        <span>{label}</span>
      </label>
      {hint ? (
        <p id={`${id}-hint`} className="pl-8 text-sm text-taupe-dark">
          {hint}
        </p>
      ) : null}
      {error ? (
        <p id={`${id}-error`} role="alert" className="pl-8 text-sm font-medium text-bordeaux">
          {error}
        </p>
      ) : null}
    </div>
  );
}
