"use client";

import { useTranslations } from "next-intl";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useId, useState } from "react";

import { ButtonLink } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { Tabs } from "@/components/ui/Tabs";
import type { City, Discipline } from "@/lib/referentials";
import { routes } from "@/lib/routes";
import {
  DEFAULT_FILTERS,
  serializeFilters,
  type DiscoverTab,
  type OpportunityFilters as Filters,
} from "@/lib/search-params";

import { OpportunityFilters } from "./OpportunityFilters";
import { OpportunityResults } from "./OpportunityResults";
import { ProjectResults } from "./ProjectResults";

export interface DiscoverViewProps {
  initialTab: DiscoverTab;
  initialFilters: Filters;
  disciplines: Discipline[];
  cities: City[];
}

/**
 * Page Découverte : onglets Annonces / Projets / Créateurs. L'état (onglet et
 * filtres) vit dans l'URL pour être partageable ; l'historique n'est pas pollué
 * (replace) sauf au changement d'onglet.
 */
export function DiscoverView({
  initialTab,
  initialFilters,
  disciplines,
  cities,
}: DiscoverViewProps) {
  const t = useTranslations("discover");
  const router = useRouter();
  const pathname = usePathname();
  const panelId = useId();
  const [tab, setTab] = useState<DiscoverTab>(initialTab);
  const [filters, setFilters] = useState<Filters>(initialFilters);

  const sync = useCallback(
    (nextTab: DiscoverTab, nextFilters: Filters, push = false) => {
      const qs = serializeFilters(nextFilters, nextTab);
      const url = qs ? `${pathname}?${qs}` : pathname;
      if (push) router.push(url, { scroll: false });
      else router.replace(url, { scroll: false });
    },
    [pathname, router],
  );

  const onFilters = useCallback(
    (next: Filters) => {
      setFilters(next);
      sync(tab, next);
    },
    [sync, tab],
  );

  const onTab = (next: DiscoverTab) => {
    setTab(next);
    sync(next, filters, true);
  };

  const reset = () => onFilters({ ...DEFAULT_FILTERS });

  return (
    <div className="flex flex-col gap-6">
      <Tabs
        label={t("title")}
        value={tab}
        onChange={onTab}
        panelId={panelId}
        items={[
          { value: "annonces", label: t("tabs.opportunities") },
          { value: "projets", label: t("tabs.projects") },
          { value: "createurs", label: t("tabs.creators") },
        ]}
      />
      <div id={panelId} role="tabpanel" tabIndex={0} className="flex flex-col gap-6 outline-none">
        {tab === "annonces" ? (
          <>
            <OpportunityFilters
              filters={filters}
              onChange={onFilters}
              disciplines={disciplines}
              cities={cities}
            />
            <OpportunityResults filters={filters} onReset={reset} />
            <p className="text-center text-xs text-taupe-dark">{t("noRanking")}</p>
          </>
        ) : null}
        {tab === "projets" ? (
          <ProjectResults
            filters={filters}
            onChange={onFilters}
            disciplines={disciplines}
            cities={cities}
          />
        ) : null}
        {tab === "createurs" ? (
          <EmptyState
            title={t("creatorsSoon")}
            body={t("creatorsSoonBody")}
            action={
              <ButtonLink href={routes.discover} variant="secondary">
                {t("tabs.opportunities")}
              </ButtonLink>
            }
          />
        ) : null}
      </div>
    </div>
  );
}
