"use client";

import { useId, useRef, type KeyboardEvent, type ReactNode } from "react";

import { cn } from "@/lib/cn";

export interface TabItem<T extends string> {
  value: T;
  label: ReactNode;
  /** Compteur optionnel affiché après le libellé. */
  count?: number;
}

export interface TabsProps<T extends string> {
  items: TabItem<T>[];
  value: T;
  onChange: (value: T) => void;
  /** Libellé accessible de la liste d'onglets. */
  label: string;
  className?: string;
  /** Identifiant du panneau associé (aria-controls). */
  panelId?: string;
}

/**
 * Onglets accessibles : `role="tablist"`, tabindex itinérant, flèches,
 * Début/Fin. Le contenu est rendu par le parent dans un élément `role="tabpanel"`.
 */
export function Tabs<T extends string>({
  items,
  value,
  onChange,
  label,
  className,
  panelId,
}: TabsProps<T>) {
  const baseId = useId();
  const refs = useRef<Array<HTMLButtonElement | null>>([]);

  const focusIndex = (index: number) => {
    const next = (index + items.length) % items.length;
    const item = items[next];
    refs.current[next]?.focus();
    if (item) onChange(item.value);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    const keys: Record<string, () => void> = {
      ArrowRight: () => focusIndex(index + 1),
      ArrowLeft: () => focusIndex(index - 1),
      Home: () => focusIndex(0),
      End: () => focusIndex(items.length - 1),
    };
    const handler = keys[event.key];
    if (handler) {
      event.preventDefault();
      handler();
    }
  };

  return (
    <div
      role="tablist"
      aria-label={label}
      className={cn("flex gap-1 overflow-x-auto border-b border-taupe/20", className)}
    >
      {items.map((item, index) => {
        const selected = item.value === value;
        return (
          <button
            key={item.value}
            ref={(el) => {
              refs.current[index] = el;
            }}
            role="tab"
            type="button"
            id={`${baseId}-tab-${item.value}`}
            aria-selected={selected}
            aria-controls={panelId}
            tabIndex={selected ? 0 : -1}
            onClick={() => onChange(item.value)}
            onKeyDown={(e) => onKeyDown(e, index)}
            className={cn(
              "relative -mb-px inline-flex min-h-touch items-center gap-2 px-4 text-sm font-medium whitespace-nowrap transition-colors sm:text-base",
              selected
                ? "border-b-2 border-gold text-brown"
                : "border-b-2 border-transparent text-taupe-dark hover:text-brown",
            )}
          >
            {item.label}
            {item.count !== undefined ? (
              <span className="rounded-full bg-ivory px-2 py-0.5 text-xs text-taupe-dark">
                {item.count}
              </span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
