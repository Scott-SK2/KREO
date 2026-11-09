import { getTranslations } from "next-intl/server";

import { ButtonLink } from "@/components/ui/Button";
import { RingsPattern } from "@/components/ui/RingsPattern";
import { routes } from "@/lib/routes";

export default async function NotFound() {
  const t = await getTranslations("common");
  return (
    <section className="kreo-container relative overflow-hidden py-24 text-center">
      <RingsPattern className="absolute top-1/2 left-1/2 size-[36rem] -translate-x-1/2 -translate-y-1/2" />
      <div className="relative">
        <p className="font-display text-7xl font-black text-gold">404</p>
        <h1 className="mt-4 text-3xl">{t("notFoundTitle")}</h1>
        <p className="mx-auto mt-3 max-w-md text-taupe-dark">{t("notFoundBody")}</p>
        <ButtonLink href={routes.home} className="mt-8">
          {t("backHome")}
        </ButtonLink>
      </div>
    </section>
  );
}
