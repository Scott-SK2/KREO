"use client";

import { useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCheck } from "lucide-react";
import { useTranslations } from "next-intl";
import Link from "next/link";

import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadMore } from "@/components/ui/LoadMore";
import { Skeleton } from "@/components/ui/Skeleton";
import { useToast } from "@/components/ui/Toast";
import { useErrorMessage } from "@/hooks/useErrorMessage";
import { api, unwrap } from "@/lib/api/client";
import { cn } from "@/lib/cn";
import { formatDateTime } from "@/lib/format";
import { cursorFromUrl } from "@/lib/search-params";

const KEY = ["notifications"] as const;

/** Lien interne sûr vers la cible d'une notification (jamais d'URL externe). */
function safeDeepLink(link: string | undefined): string | null {
  if (!link) return null;
  if (link.startsWith("/") && !link.startsWith("//")) return link;
  try {
    const url = new URL(link);
    if (typeof window !== "undefined" && url.origin === window.location.origin) {
      return `${url.pathname}${url.search}`;
    }
  } catch {
    return null;
  }
  return null;
}

/** Notifications : non-lues en évidence, « tout marquer comme lu », lien profond. */
export function NotificationList() {
  const t = useTranslations();
  const describeError = useErrorMessage();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const query = useInfiniteQuery({
    queryKey: KEY,
    initialPageParam: undefined as string | undefined,
    queryFn: async ({ pageParam }) =>
      unwrap(await api.GET("/api/v1/notifications", { params: { query: { cursor: pageParam } } })),
    getNextPageParam: (last) => cursorFromUrl(last.next),
  });

  const markAll = useMutation({
    mutationFn: async () => unwrap(await api.POST("/api/v1/notifications/read", { body: {} })),
    onSuccess: async () => {
      toast(t("notifications.allRead"), "success");
      await queryClient.invalidateQueries({ queryKey: KEY });
    },
    onError: (error) => toast(describeError(error), "error"),
  });

  const markOne = useMutation({
    mutationFn: async (id: string) =>
      unwrap(await api.POST("/api/v1/notifications/read", { body: { ids: [id] } })),
    onSettled: () => queryClient.invalidateQueries({ queryKey: KEY }),
  });

  const items = query.data?.pages.flatMap((p) => p.results) ?? [];
  const unread = items.filter((n) => !n.read_at).length;

  if (query.isPending) {
    return (
      <div className="flex flex-col gap-2" aria-busy="true">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
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
    return <EmptyState title={t("notifications.empty")} />;
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-taupe-dark" aria-live="polite">
          {t("notifications.unread", { count: unread })}
        </p>
        <Button
          variant="ghost"
          size="sm"
          icon={<CheckCheck aria-hidden="true" className="size-4" strokeWidth={1.5} />}
          disabled={unread === 0}
          loading={markAll.isPending}
          onClick={() => markAll.mutate()}
        >
          {t("notifications.markAllRead")}
        </Button>
      </div>
      <ul className="divide-y divide-taupe/10 overflow-hidden rounded-xl border border-taupe/15 bg-white">
        {items.map((n) => {
          const isUnread = !n.read_at;
          const href = safeDeepLink(n.deep_link);
          const content = (
            <>
              <span
                aria-hidden="true"
                className={cn(
                  "mt-2 size-2 shrink-0 rounded-full",
                  isUnread ? "bg-bordeaux" : "bg-transparent",
                )}
              />
              <span className="min-w-0 flex-1">
                <span
                  className={cn("block text-sm text-brown", isUnread ? "font-bold" : "font-medium")}
                >
                  {n.title}
                  {isUnread ? <span className="sr-only"> ({t("common.new")})</span> : null}
                </span>
                <span className="block text-xs text-taupe-dark">
                  {formatDateTime(n.created_at)}
                </span>
              </span>
            </>
          );
          return (
            <li key={n.id} className={cn(isUnread && "bg-gold/5")}>
              {href ? (
                <Link
                  href={href}
                  onClick={() => {
                    if (isUnread) markOne.mutate(n.id);
                  }}
                  className="flex min-h-touch items-start gap-3 px-4 py-3 hover:bg-ivory/60"
                >
                  {content}
                </Link>
              ) : (
                <div className="flex min-h-touch items-start gap-3 px-4 py-3">{content}</div>
              )}
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
    </div>
  );
}
