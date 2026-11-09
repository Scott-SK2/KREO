"use client";

import { X } from "lucide-react";
import { useEffect, useId, useRef, type ReactNode } from "react";

import { cn } from "@/lib/cn";

export interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: ReactNode;
  description?: ReactNode;
  children: ReactNode;
  /** Libellé du bouton de fermeture (t("common.close")). */
  closeLabel: string;
  className?: string;
}

/**
 * Boîte de dialogue modale sur `<dialog>` natif : piège de focus et Échap
 * fournis par le navigateur, fermeture au clic sur le fond, retour du focus
 * à l'élément déclencheur à la fermeture.
 */
export function Dialog({
  open,
  onClose,
  title,
  description,
  children,
  closeLabel,
  className,
}: DialogProps) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const descId = useId();

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
      const focusable = dialog.querySelector<HTMLElement>(
        "input, select, textarea, button:not([data-dialog-close])",
      );
      (focusable ?? dialog.querySelector<HTMLElement>("[data-dialog-close]"))?.focus();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const { overflow } = document.body.style;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = overflow;
    };
  }, [open]);

  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      aria-describedby={description ? descId : undefined}
      onClose={onClose}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={(event) => {
        if (event.target === ref.current) onClose();
      }}
      className={cn(
        "m-auto w-[min(100%-2rem,32rem)] rounded-2xl border border-taupe/20 bg-paper p-0 text-ink shadow-lg backdrop:bg-ink/55",
        className,
      )}
    >
      <div className="p-6 sm:p-8" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between gap-4">
          <h2 id={titleId} className="text-xl leading-tight sm:text-2xl">
            {title}
          </h2>
          <button
            type="button"
            data-dialog-close
            onClick={onClose}
            aria-label={closeLabel}
            className="-mt-1 -mr-2 inline-flex size-11 shrink-0 items-center justify-center rounded-full text-taupe-dark hover:bg-ivory"
          >
            <X aria-hidden="true" className="size-5" strokeWidth={1.5} />
          </button>
        </div>
        {description ? (
          <p id={descId} className="mt-2 text-sm text-taupe-dark">
            {description}
          </p>
        ) : null}
        <div className="mt-5">{children}</div>
      </div>
    </dialog>
  );
}
