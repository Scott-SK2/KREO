"use client";

import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import Link from "next/link";

import { Avatar } from "@/components/ui/Avatar";
import { Button, ButtonLink } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton } from "@/components/ui/Skeleton";
import { useErrorMessage } from "@/hooks/useErrorMessage";
import { api, unwrap } from "@/lib/api/client";
import { cn } from "@/lib/cn";
import { formatDateTime } from "@/lib/format";
import { routes } from "@/lib/routes";

export const CONVERSATIONS_KEY = ["conversations"] as const;

/** Liste des conversations avec compteur de non-lus ; rafraîchie toutes les 30 s. */
export function ConversationList({ activeId }: { activeId?: string }) {
  const t = useTranslations();
  const describeError = useErrorMessage();
  const query = useQuery({
    queryKey: CONVERSATIONS_KEY,
    queryFn: async () => unwrap(await api.GET("/api/v1/conversations")),
    refetchInterval: 30_000,
  });

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
  if (!query.data.length) {
    return (
      <EmptyState
        title={t("messages.empty")}
        body={t("application.emptyHint")}
        action={<ButtonLink href={routes.applications}>{t("nav.myApplications")}</ButtonLink>}
      />
    );
  }

  const unread = query.data.reduce((sum, c) => sum + c.unread_count, 0);

  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm text-taupe-dark" aria-live="polite">
        {t("messages.unread", { count: unread })}
      </p>
      <ul className="divide-y divide-taupe/10 overflow-hidden rounded-xl border border-taupe/15 bg-white">
        {query.data.map((c) => {
          const active = c.id === activeId;
          const hasUnread = c.unread_count > 0;
          return (
            <li key={c.id}>
              <Link
                href={routes.conversation(c.id)}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex min-h-touch items-center gap-3 px-4 py-3 hover:bg-ivory/60",
                  active && "bg-ivory",
                )}
              >
                <Avatar name={c.project_title} size="sm" />
                <span className="min-w-0 flex-1">
                  <span className="flex items-center justify-between gap-2">
                    <span
                      className={cn(
                        "truncate text-sm text-brown",
                        hasUnread ? "font-bold" : "font-medium",
                      )}
                    >
                      {c.role_title} · {c.project_title}
                    </span>
                    {c.last_message_at ? (
                      <span className="shrink-0 text-xs text-taupe-dark">
                        {formatDateTime(c.last_message_at)}
                      </span>
                    ) : null}
                  </span>
                  <span className="mt-0.5 flex items-center justify-between gap-2">
                    <span className="truncate text-xs text-taupe-dark">
                      {c.last_message?.body ?? t("messages.noMessages")}
                    </span>
                    {hasUnread ? (
                      <span className="inline-flex min-w-5 items-center justify-center rounded-full bg-bordeaux px-1.5 py-0.5 text-[11px] font-bold text-paper">
                        {c.unread_count}
                        <span className="sr-only">
                          {" "}
                          {t("messages.unread", { count: c.unread_count })}
                        </span>
                      </span>
                    ) : null}
                  </span>
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
