"use client";

import { CheckCircle2, Info, TriangleAlert, X } from "lucide-react";
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { cn } from "@/lib/cn";

export type ToastTone = "info" | "success" | "error";

export interface ToastItem {
  id: number;
  tone: ToastTone;
  message: string;
}

interface ToastContextValue {
  toast: (message: string, tone?: ToastTone) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

const icons = { info: Info, success: CheckCircle2, error: TriangleAlert };
const toneClasses: Record<ToastTone, string> = {
  info: "border-taupe/30",
  success: "border-success/40",
  error: "border-bordeaux/40",
};

/**
 * Fournit `toast()` et rend une région `aria-live` : les messages courts sont
 * annoncés aux lecteurs d'écran et disparaissent après 6 s (les erreurs restent 10 s).
 */
export function ToastProvider({
  children,
  closeLabel = "Fermer",
}: {
  children: ReactNode;
  closeLabel?: string;
}) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const counter = useRef(0);

  const dismiss = useCallback((id: number) => {
    setItems((list) => list.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback(
    (message: string, tone: ToastTone = "info") => {
      const id = ++counter.current;
      setItems((list) => [...list, { id, tone, message }]);
      window.setTimeout(() => dismiss(id), tone === "error" ? 10_000 : 6_000);
    },
    [dismiss],
  );

  const value = useMemo(() => ({ toast }), [toast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        aria-live="polite"
        aria-atomic="false"
        className="pointer-events-none fixed inset-x-0 bottom-4 z-50 flex flex-col items-center gap-2 px-4"
      >
        {items.map((item) => {
          const Icon = icons[item.tone];
          return (
            <div
              key={item.id}
              role={item.tone === "error" ? "alert" : "status"}
              className={cn(
                "pointer-events-auto flex w-full max-w-md items-start gap-3 rounded-lg border bg-white px-4 py-3 text-sm text-brown shadow-lg",
                toneClasses[item.tone],
              )}
            >
              <Icon
                aria-hidden="true"
                className={cn(
                  "mt-0.5 size-5 shrink-0",
                  item.tone === "error" ? "text-bordeaux" : "text-taupe-dark",
                )}
                strokeWidth={1.5}
              />
              <p className="flex-1">{item.message}</p>
              <button
                type="button"
                onClick={() => dismiss(item.id)}
                aria-label={closeLabel}
                className="-m-2 inline-flex size-11 shrink-0 items-center justify-center rounded-full text-taupe-dark hover:bg-ivory"
              >
                <X aria-hidden="true" className="size-4" strokeWidth={1.5} />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

/** Accès à `toast(message, tone)` ; lève hors du ToastProvider. */
export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast doit être utilisé dans un ToastProvider.");
  return ctx;
}
