"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";

import { OpportunityCard } from "@/components/opportunities/OpportunityCard";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadMore } from "@/components/ui/LoadMore";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { useErrorMessage } from "@/hooks/useErrorMessage";
import { api, unwrap } from "@/lib/api/client";
import {
  cursorFromUrl,
  toOpportunityQuery,
  type OpportunityFilters as Filters,
} from "@/lib/search-params";

/** Liste d'annonces paginée par curseur, pilotée par les filtres de l'URL. */
export function OpportunityResults({
  filters,
  onReset,
}: {
  filters: Filters;
  onReset: () => void;
}) {
  const t = useTranslations();
  const describeError = useErrorMessage();
  const query = useInfiniteQuery({
    queryKey: ["opportunities", filters],
    initialPageParam: undefined as string | undefined,
    queryFn: async ({ pageParam }) =>
      unwrap(
        await api.GET("/api/v1/opportunities", {
          params: { query: { ...toOpportunityQuery(filters), cursor: pageParam } },
        }),
      ),
    getNextPageParam: (last) => cursorFromUrl(last.next),
  });

  const items = query.data?.pages.flatMap((p) => p.results) ?? [];

  if (query.isPending) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-busy="true">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  if (query.isError) {
    return (
      <EmptyState
        title={t("common.errorTitle")}
        body={describeError(query.error)}
        action={
          <Button variant="secondary" onClick={() => void query.refetch()}>
            {t("common.retry")}
          </Button>
        }
      />
    );
  }

  if (!items.length) {
    return (
      <EmptyState
        title={t("discover.emptyTitle")}
        body={t("discover.emptyBody")}
        action={
          <Button variant="secondary" onClick={onReset}>
            {t("discover.reset")}
          </Button>
        }
      />
    );
  }

  return (
    <>
      <p className="text-sm text-taupe-dark" aria-live="polite">
        {t("discover.results", { count: items.length })}
        {query.hasNextPage ? "+" : ""}
      </p>
      <ul className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((o) => (
          <li key={o.id} className="relative">
            <OpportunityCard opportunity={o} />
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
  );
}
