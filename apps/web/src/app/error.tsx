"use client";

import { useTranslations } from "next-intl";
import { useEffect } from "react";

import { Button, ButtonLink } from "@/components/ui/Button";
import { routes } from "@/lib/routes";

export default function RootError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const t = useTranslations("common");
  useEffect(() => {
    console.error(error);
  }, [error]);
  return (
    <section className="kreo-container py-24 text-center">
      <h1 className="text-3xl">{t("errorTitle")}</h1>
      <p className="mx-auto mt-3 max-w-md text-taupe-dark">{t("error")}</p>
      <div className="mt-8 flex justify-center gap-3">
        <Button onClick={reset}>{t("retry")}</Button>
        <ButtonLink href={routes.home} variant="secondary">
          {t("backHome")}
        </ButtonLink>
      </div>
    </section>
  );
}
