import type { ComponentPropsWithoutRef, ReactNode } from "react";

import { cn } from "@/lib/cn";

import { FieldWrapper, controlBorder, controlClasses, describedBy } from "./FieldWrapper";

export interface TextareaProps extends Omit<ComponentPropsWithoutRef<"textarea">, "id"> {
  id: string;
  label: ReactNode;
  hint?: ReactNode;
  error?: ReactNode;
  optional?: string;
}

/** Zone de texte multi-lignes, mêmes garanties d'accessibilité que TextField. */
export function Textarea({ id, label, hint, error, optional, className, ...rest }: TextareaProps) {
  return (
    <FieldWrapper id={id} label={label} hint={hint} error={error} optional={optional}>
      <textarea
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(id, hint, error)}
        className={cn(controlClasses, controlBorder(error), "min-h-28 resize-y", className)}
        {...rest}
      />
    </FieldWrapper>
  );
}
