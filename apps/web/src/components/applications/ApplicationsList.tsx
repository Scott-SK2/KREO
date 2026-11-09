"use client";

import type { components } from "@kreo/api-client";
import { useInfiniteQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { useId, useMemo, useState } from "react";

import { StatusBadge } from "@/components/ui/Badge";
import { Button, ButtonLink } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadMore } from "@/components/ui/LoadMore";
import { Skeleton } from "@/components/ui/Skeleton";
import { Tabs } from "@/components/ui/Tabs";
import { useErrorMessage } from "@/hooks/useErrorMessage";
import { api, unwrap } from "@/lib/api/client";
import { formatDate } from "@/lib/format";
import { routes } from "@/lib/routes";
import { cursorFromUrl } from "@/lib/search-params";

type Status = components["schemas"]["ApplicationStatusEnum"];
type Filter = "all" | "ongoing" | "offered" | "accepted" | "closed";

const FILTERS: Record<Exclude<Filter, "all">, Status[]> = {
  ongoing: ["submitted", "viewed", "shortlisted", "audition"],
  offered: ["offered"],
  accepted: ["accepted"],
  closed: ["declined", "rejected", "withdrawn"],
};

/** Mes candidatures : onglets par étape, liste paginée, lien vers le détail. */
export function ApplicationsList() {
  const t = useTranslations();
  const describeError = useErrorMessage();
  const panelId = useId();
  const [filter, setFilter] = useState<Filter>("all");

  const query = useInfiniteQuery({
    queryKey: ["applications", "mine"],
    initialPageParam: undefined as string | undefined,
    queryFn: async ({ pageParam }) =>
      unwrap(
        await api.GET("/api/v1/me/applications", {
          params: { query: { cursor: pageParam, page_size: 20 } },
        }),
      ),
    getNextPageParam: (last) => cursorFromUrl(last.next),
  });

  const all = useMemo(() => query.data?.pages.flatMap((p) => p.results) ?? [], [query.data]);
  const visible =
    filter === "all" ? all : all.filter((a) => FILTERS[filter].includes(a.status ?? "submitted"));
  const count = (f: Filter) =>
    f === "all"
      ? all.length
      : all.filter((a) => FILTERS[f].includes(a.status ?? "submitted")).length;

  return (
    <div className="flex flex-col gap-6">
      <Tabs
        label={t("nav.myApplications")}
        value={filter}
        onChange={setFilter}
        panelId={panelId}
        items={[
          { value: "all", label: t("application.all"), count: count("all") },
          { value: "ongoing", label: t("application.status.submitted"), count: count("ongoing") },
          { value: "offered", label: t("application.status.offered"), count: count("offered") },
          { value: "accepted", label: t("application.status.accepted"), count: count("accepted") },
          { value: "closed", label: t("application.status.rejected"), count: count("closed") },
        ]}
      />
      <div id={panelId} role="tabpanel" tabIndex={0} className="outline-none">
        {query.isPending ? (
          <div className="flex flex-col gap-3" aria-busy="true">
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
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
        ) : !visible.length ? (
          <EmptyState
            title={t("application.empty")}
            body={t("application.emptyHint")}
            action={<ButtonLink href={routes.discover}>{t("nav.discover")}</ButtonLink>}
          />
        ) : (
          <>
            <ul className="flex flex-col gap-3">
              {visible.map((a) => {
                const status = a.status ?? "submitted";
                return (
                  <li key={a.id}>
                    <Card interactive padding="sm" className="relative">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div className="min-w-0">
                          <h3 className="text-base normal-case tracking-normal">
                            <Link
                              href={routes.application(a.id)}
                              className="after:absolute after:inset-0 after:rounded-xl focus-visible:outline-none"
                            >
                              {a.role.title}
                            </Link>
                          </h3>
                          <p className="mt-1 truncate text-sm text-taupe-dark">
                            {a.opportunity_title} · {a.project_title}
                          </p>
                          <p className="mt-1 text-xs text-taupe-dark">
                            {t("application.submittedOn", { date: formatDate(a.submitted_at) })}
                          </p>
                        </div>
                        <StatusBadge status={status} label={t(`application.status.${status}`)} />
                      </div>
                    </Card>
                  </li>
                );
              })}
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
    </div>
  );
}
