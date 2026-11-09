import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

import { RingsPattern } from "./RingsPattern";

export interface EmptyStateProps {
  title: ReactNode;
  body?: ReactNode;
  action?: ReactNode;
  className?: string;
}

/** État vide chaleureux : titre, phrase utile et action possible. */
export function EmptyState({ title, body, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl border border-dashed border-taupe/30 bg-ivory/50 px-6 py-10 text-center",
        className,
      )}
    >
      <RingsPattern className="absolute -top-16 -right-16 size-56 opacity-60" rings={6} />
      <div className="relative">
        <h3 className="text-lg normal-case tracking-normal">{title}</h3>
        {body ? <p className="mx-auto mt-2 max-w-md text-sm text-taupe-dark">{body}</p> : null}
        {action ? <div className="mt-5 flex justify-center">{action}</div> : null}
      </div>
    </div>
  );
}
