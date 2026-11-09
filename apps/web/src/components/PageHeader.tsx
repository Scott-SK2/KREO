import type { ReactNode } from "react";

import { RingsPattern } from "@/components/ui/RingsPattern";

/** Bandeau de titre avec le motif d'ondes, commun aux pages intérieures. */
export function PageHeader({
  title,
  lead,
  actions,
  eyebrow,
}: {
  title: ReactNode;
  lead?: ReactNode;
  actions?: ReactNode;
  eyebrow?: ReactNode;
}) {
  return (
    <section className="relative overflow-hidden border-b border-taupe/10 bg-ivory/40">
      <RingsPattern className="absolute -top-40 -right-24 size-[28rem]" />
      <div className="kreo-container relative flex flex-col gap-4 py-10 sm:flex-row sm:items-end sm:justify-between">
        <div>
          {eyebrow ? (
            <p className="mb-2 text-xs font-medium tracking-caps text-taupe-dark uppercase">
              {eyebrow}
            </p>
          ) : null}
          <h1 className="text-3xl sm:text-4xl">{title}</h1>
          {lead ? <p className="mt-3 max-w-2xl text-taupe-dark">{lead}</p> : null}
        </div>
        {actions ? <div className="flex shrink-0 gap-2">{actions}</div> : null}
      </div>
    </section>
  );
}
