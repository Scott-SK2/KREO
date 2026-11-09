import type { ReactNode } from "react";

import { RingsPattern } from "@/components/ui/RingsPattern";

/** Gabarit des pages d'authentification : carte centrée sur fond d'ondes. */
export function AuthCard({
  title,
  intro,
  children,
  footer,
}: {
  title: ReactNode;
  intro?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <section className="relative overflow-hidden py-12 sm:py-20">
      <RingsPattern className="absolute -top-40 -left-40 size-[36rem]" rings={12} />
      <div className="kreo-container relative">
        <div className="mx-auto w-full max-w-md rounded-2xl border border-taupe/15 bg-white p-6 shadow-md sm:p-8">
          <h1 className="text-2xl sm:text-3xl">{title}</h1>
          {intro ? <p className="mt-3 text-sm text-taupe-dark">{intro}</p> : null}
          <div className="mt-6">{children}</div>
          {footer ? (
            <div className="mt-6 border-t border-taupe/10 pt-5 text-sm text-taupe-dark">
              {footer}
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
