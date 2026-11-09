import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { DiscoverView } from "@/components/discover/DiscoverView";
import { PageHeader } from "@/components/PageHeader";
import { publicApi, unwrap } from "@/lib/api/server";
import type { City, Discipline } from "@/lib/referentials";
import { parseFilters, parseTab } from "@/lib/search-params";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("discover");
  return { title: t("title"), description: t("emptyBody") };
}

async function referentials(): Promise<{ disciplines: Discipline[]; cities: City[] }> {
  const api = publicApi(3600);
  try {
    const [disciplines, cities] = await Promise.all([
      api.GET("/api/v1/disciplines").then(unwrap),
      api.GET("/api/v1/cities").then(unwrap),
    ]);
    return { disciplines, cities };
  } catch {
    return { disciplines: [], cities: [] };
  }
}

export default async function DiscoverPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const t = await getTranslations("discover");
  const { disciplines, cities } = await referentials();
  const tab = parseTab(params);
  const filters = parseFilters(params);

  return (
    <>
      <PageHeader title={t("title")} lead={t("noRanking")} />
      <section className="kreo-container py-8">
        <DiscoverView
          key={`${tab}-${JSON.stringify(filters)}`}
          initialTab={tab}
          initialFilters={filters}
          disciplines={disciplines}
          cities={cities}
        />
      </section>
    </>
  );
}
