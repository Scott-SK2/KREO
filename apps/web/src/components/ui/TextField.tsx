import type { ComponentPropsWithoutRef, ReactNode } from "react";

import { cn } from "@/lib/cn";

import { FieldWrapper, controlBorder, controlClasses, describedBy } from "./FieldWrapper";

export interface TextFieldProps extends Omit<ComponentPropsWithoutRef<"input">, "id"> {
  id: string;
  label: ReactNode;
  hint?: ReactNode;
  error?: ReactNode;
  optional?: string;
  /** Élément affiché à droite dans le champ (ex. bouton afficher/masquer). */
  trailing?: ReactNode;
  wrapperClassName?: string;
}

/**
 * Champ texte avec étiquette, indice et erreur reliés par aria-describedby ;
 * `aria-invalid` est posé quand une erreur est présente.
 */
export function TextField({
  id,
  label,
  hint,
  error,
  optional,
  trailing,
  className,
  wrapperClassName,
  ...rest
}: TextFieldProps) {
  return (
    <FieldWrapper
      id={id}
      label={label}
      hint={hint}
      error={error}
      optional={optional}
      className={wrapperClassName}
    >
      <div className="relative">
        <input
          id={id}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy(id, hint, error)}
          className={cn(controlClasses, controlBorder(error), trailing ? "pr-12" : undefined, className)}
          {...rest}
        />
        {trailing ? (
          <div className="absolute inset-y-0 right-1 flex items-center">{trailing}</div>
        ) : null}
      </div>
    </FieldWrapper>
  );
}
