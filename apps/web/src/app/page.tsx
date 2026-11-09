import type { components } from "@kreo/api-client";
import { Award, Clapperboard, Users } from "lucide-react";
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { OpportunityCard } from "@/components/opportunities/OpportunityCard";
import { ButtonLink } from "@/components/ui/Button";
import { RingsPattern } from "@/components/ui/RingsPattern";
import { publicApi, unwrap } from "@/lib/api/server";
import { routes } from "@/lib/routes";

export const revalidate = 60;

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations();
  return {
    title: { absolute: `KREO — ${t("brand.slogan")}` },
    description: t("home.metaDescription"),
    alternates: { canonical: "/" },
  };
}

async function latestOpportunities(): Promise<components["schemas"]["OpportunityList"][]> {
  try {
    const api = publicApi(60);
    const page = unwrap(
      await api.GET("/api/v1/opportunities", { params: { query: { page_size: 6 } } }),
    );
    return page.results.slice(0, 6);
  } catch {
    return [];
  }
}

export default async function HomePage() {
  const t = await getTranslations();
  const opportunities = await latestOpportunities();

  const pillars = [
    { key: "find", icon: Users },
    { key: "make", icon: Clapperboard },
    { key: "keep", icon: Award },
  ] as const;

  return (
    <>
      <section className="relative overflow-hidden">
        <RingsPattern
          className="absolute top-1/2 -right-40 size-[44rem] -translate-y-1/2 sm:-right-24"
          rings={12}
        />
        <RingsPattern className="absolute -bottom-56 -left-32 size-[30rem]" rings={8} />
        <div className="kreo-container relative py-20 sm:py-28">
          <p className="mb-4 text-xs font-medium tracking-caps text-taupe-dark uppercase">
            {t("home.betaNotice")}
          </p>
          <h1 className="max-w-3xl text-4xl leading-[1.05] sm:text-5xl lg:text-6xl">
            {t("home.title")}
          </h1>
          <p className="mt-5 max-w-xl text-lg font-medium text-taupe-dark">{t("brand.support")}</p>
          <p className="mt-4 max-w-2xl text-base leading-relaxed text-brown">{t("home.lead")}</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <ButtonLink href={routes.discover} size="lg">
              {t("home.ctaDiscover")}
            </ButtonLink>
            <ButtonLink href={routes.register} variant="secondary" size="lg">
              {t("home.ctaJoin")}
            </ButtonLink>
          </div>
          <p className="mt-6 text-sm text-taupe-dark">{t("home.launchDisciplines")}</p>
        </div>
      </section>

      <section aria-labelledby="piliers" className="kreo-container py-12">
        <h2 id="piliers" className="sr-only">
          {t("brand.support")}
        </h2>
        <div className="grid gap-4 md:grid-cols-3">
          {pillars.map(({ key, icon: Icon }) => (
            <article key={key} className="rounded-xl border border-taupe/15 bg-white p-6 shadow-sm">
              <span className="inline-flex size-11 items-center justify-center rounded-full bg-ivory text-taupe-dark">
                <Icon aria-hidden="true" className="size-5" strokeWidth={1.5} />
              </span>
              <h3 className="mt-4 text-xl">{t(`home.pillars.${key}.title`)}</h3>
              <p className="mt-2 text-sm leading-relaxed text-taupe-dark">
                {t(`home.pillars.${key}.body`)}
              </p>
            </article>
          ))}
        </div>
      </section>

      <section aria-labelledby="dernieres" className="kreo-container py-12">
        <div className="flex items-end justify-between gap-4">
          <h2 id="dernieres" className="text-2xl sm:text-3xl">
            {t("home.latestOpportunities")}
          </h2>
          <ButtonLink href={routes.discover} variant="ghost" size="sm">
            {t("common.seeAll")}
          </ButtonLink>
        </div>
        {opportunities.length ? (
          <ul className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {opportunities.map((o) => (
              <li key={o.id} className="relative">
                <OpportunityCard opportunity={o} />
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-6 text-taupe-dark">{t("discover.emptyBody")}</p>
        )}
      </section>

      <section className="kreo-container pb-12">
        <div className="relative overflow-hidden rounded-2xl bg-ink px-6 py-10 text-paper sm:px-10">
          <RingsPattern
            className="absolute -top-32 -right-20 size-96"
            stroke="var(--kreo-color-gold)"
          />
          <div className="relative max-w-2xl">
            <p className="text-lg font-medium">{t("home.free")}</p>
            <p className="mt-2 text-sm text-paper/80">{t("discover.noRanking")}</p>
            <p className="mt-6 text-sm text-gold">{t("home.betaNotice")}</p>
          </div>
        </div>
      </section>
    </>
  );
}
