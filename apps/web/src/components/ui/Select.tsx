import { ChevronDown } from "lucide-react";
import type { ComponentPropsWithoutRef, ReactNode } from "react";

import { cn } from "@/lib/cn";

import { FieldWrapper, controlBorder, controlClasses, describedBy } from "./FieldWrapper";

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectGroup {
  label: string;
  options: SelectOption[];
}

export interface SelectProps extends Omit<ComponentPropsWithoutRef<"select">, "id"> {
  id: string;
  label: ReactNode;
  hint?: ReactNode;
  error?: ReactNode;
  optional?: string;
  /** Option vide affichée en tête (ex. « Toutes les communes »). */
  placeholder?: string;
  options?: SelectOption[];
  groups?: SelectGroup[];
}

/** Liste déroulante native (clavier et lecteurs d'écran garantis). */
export function Select({
  id,
  label,
  hint,
  error,
  optional,
  placeholder,
  options = [],
  groups = [],
  className,
  ...rest
}: SelectProps) {
  return (
    <FieldWrapper id={id} label={label} hint={hint} error={error} optional={optional}>
      <div className="relative">
        <select
          id={id}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy(id, hint, error)}
          className={cn(controlClasses, controlBorder(error), "appearance-none pr-10", className)}
          {...rest}
        >
          {placeholder !== undefined ? <option value="">{placeholder}</option> : null}
          {options.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
          {groups.map((g) => (
            <optgroup key={g.label} label={g.label}>
              {g.options.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
        <ChevronDown
          aria-hidden="true"
          className="pointer-events-none absolute top-1/2 right-3 size-4 -translate-y-1/2 text-taupe-dark"
          strokeWidth={1.5}
        />
      </div>
    </FieldWrapper>
  );
}
