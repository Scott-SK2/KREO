"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useId } from "react";

import { ProjectCard } from "@/components/projects/ProjectCard";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadMore } from "@/components/ui/LoadMore";
import { Select } from "@/components/ui/Select";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { useErrorMessage } from "@/hooks/useErrorMessage";
import { api, unwrap } from "@/lib/api/client";
import { cityOptions, groupDisciplines, type City, type Discipline } from "@/lib/referentials";
import { cursorFromUrl, type OpportunityFilters as Filters } from "@/lib/search-params";

export interface ProjectResultsProps {
  filters: Filters;
  onChange: (filters: Filters) => void;
  disciplines: Discipline[];
  cities: City[];
}

/** Onglet Projets : filtres discipline/commune (partagés dans l'URL) et liste paginée. */
export function ProjectResults({ filters, onChange, disciplines, cities }: ProjectResultsProps) {
  const t = useTranslations();
  const describeError = useErrorMessage();
  const id = useId();
  const discipline = filters.disciplines[0];
  const groups = groupDisciplines(disciplines);

  const query = useInfiniteQuery({
    queryKey: ["projects", { discipline, city: filters.city, q: filters.q }],
    initialPageParam: undefined as string | undefined,
    queryFn: async ({ pageParam }) =>
      unwrap(
        await api.GET("/api/v1/projects", {
          params: {
            query: {
              discipline,
              city: filters.city ?? undefined,
              q: filters.q || undefined,
              cursor: pageParam,
            },
          },
        }),
      ),
    getNextPageParam: (last) => cursorFromUrl(last.next),
  });

  const items = query.data?.pages.flatMap((p) => p.results) ?? [];

  return (
    <div className="flex flex-col gap-6">
      <div className="grid gap-3 sm:grid-cols-2">
        <Select
          id={`${id}-discipline`}
          label={t("discover.discipline")}
          placeholder={t("discover.allDisciplines")}
          value={discipline ?? ""}
          onChange={(e) =>
            onChange({ ...filters, disciplines: e.target.value ? [e.target.value] : [] })
          }
          groups={groups.map((g) => ({
            label: g.parent?.label ?? "—",
            options: (g.parent ? [g.parent, ...g.children] : g.children).map((d) => ({
              value: d.slug,
              label: d.label,
            })),
          }))}
        />
        <Select
          id={`${id}-city`}
          label={t("discover.city")}
          placeholder={t("discover.allCities")}
          value={filters.city === null ? "" : String(filters.city)}
          onChange={(e) =>
            onChange({ ...filters, city: e.target.value ? Number(e.target.value) : null })
          }
          options={cityOptions(cities)}
        />
      </div>

      {query.isPending ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-busy="true">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      ) : query.isError ? (
        <EmptyState
          title={t("common.errorTitle")}
          body={describeError(query.error)}
          action={
            <Button variant="secondary" onClick={() => void query.refetch()}>
              {t("common.retry")}
            </Button>
          }
        />
      ) : !items.length ? (
        <EmptyState
          title={t("discover.projectsEmptyTitle")}
          body={t("discover.projectsEmptyBody")}
        />
      ) : (
        <>
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((p) => (
              <li key={p.id} className="relative">
                <ProjectCard project={p} />
              </li>
            ))}
          </ul>
          <LoadMore
            hasMore={Boolean(query.hasNextPage)}
            loading={query.isFetchingNextPage}
            onLoadMore={() => void query.fetchNextPage()}
            label={t("discover.loadMore")}
          />
        </>
      )}
    </div>
  );
}
