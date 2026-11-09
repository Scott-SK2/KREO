"use client";

import type { components } from "@kreo/api-client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { useToast } from "@/components/ui/Toast";
import { useErrorMessage } from "@/hooks/useErrorMessage";
import { api, unwrap } from "@/lib/api/client";

type Preference = components["schemas"]["NotificationPreference"];
type Channel = "in_app" | "email" | "push";
const CHANNELS: Channel[] = ["in_app", "email", "push"];
const KEY = ["notification-preferences"] as const;

/** Clé API d'événement → clé i18n (`account.events.*`, sans point). */
const EVENT_LABELS = {
  "application.new": "application_new",
  "application.viewed": "application_viewed",
  "application.shortlisted": "application_shortlisted",
  "application.audition": "application_audition",
  "application.offered": "application_offered",
  "application.accepted": "application_accepted",
  "application.declined": "application_declined",
  "application.rejected": "application_rejected",
  "message.new": "message_new",
  "credit.proposed": "credit_proposed",
  "credit.confirmed": "credit_confirmed",
  "credit.disputed": "credit_disputed",
  "project.invitation": "project_invitation",
  "applications.reminder_5d": "applications_reminder_5d",
  "opportunity.expiring_2d": "opportunity_expiring_2d",
  "saved_search.match": "saved_search_match",
  "moderation.decision": "moderation_decision",
  "moderation.appeal_decided": "moderation_appeal_decided",
} as const;
type EventKey = keyof typeof EVENT_LABELS;
const isEventKey = (k: string): k is EventKey => k in EVENT_LABELS;

/** Grille des préférences par événement et canal ; les e-mails obligatoires sont verrouillés. */
export function NotificationPreferences() {
  const t = useTranslations("account");
  const tCommon = useTranslations("common");
  const describeError = useErrorMessage();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState<Preference[]>([]);

  const query = useQuery({
    queryKey: KEY,
    queryFn: async () => unwrap(await api.GET("/api/v1/me/notification-preferences")),
  });

  useEffect(() => {
    if (query.data) setDraft(query.data);
  }, [query.data]);

  const save = useMutation({
    mutationFn: async () =>
      unwrap(
        await api.PUT("/api/v1/me/notification-preferences", {
          body: draft.map(({ event_key, in_app, email, push }) => ({
            event_key,
            in_app,
            email,
            push,
          })),
        }),
      ),
    onSuccess: (data) => {
      queryClient.setQueryData(KEY, data);
      toast(t("saved"), "success");
    },
    onError: (error) => toast(describeError(error), "error"),
  });

  const toggle = (eventKey: string, channel: Channel) =>
    setDraft((list) =>
      list.map((p) => (p.event_key === eventKey ? { ...p, [channel]: !p[channel] } : p)),
    );

  if (query.isPending) return <Skeleton className="h-64 w-full" />;
  if (query.isError) {
    return (
      <p role="alert" className="text-sm text-bordeaux">
        {describeError(query.error)}
      </p>
    );
  }

  const dirty = JSON.stringify(draft) !== JSON.stringify(query.data);

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-taupe-dark">{t("preferencesHint")}</p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs tracking-caps text-taupe-dark uppercase">
              <th scope="col" className="py-2 pr-4 font-medium">
                {t("preferences")}
              </th>
              {CHANNELS.map((c) => (
                <th key={c} scope="col" className="px-2 py-2 text-center font-medium">
                  {t(`channels.${c}`)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-taupe/10">
            {draft.map((p) => (
              <tr key={p.event_key}>
                <th scope="row" className="py-2 pr-4 text-left font-normal text-brown">
                  {isEventKey(p.event_key) ? t(`events.${EVENT_LABELS[p.event_key]}`) : p.event_key}
                </th>
                {CHANNELS.map((c) => {
                  const locked = c === "email" && p.mandatory_email;
                  const label = `${isEventKey(p.event_key) ? t(`events.${EVENT_LABELS[p.event_key]}`) : p.event_key} — ${t(`channels.${c}`)}${locked ? ` (${t("mandatory")})` : ""}`;
                  return (
                    <td key={c} className="px-2 py-1 text-center">
                      <label className="inline-flex size-11 cursor-pointer items-center justify-center">
                        <input
                          type="checkbox"
                          className="size-5 accent-taupe disabled:cursor-not-allowed"
                          checked={locked ? true : Boolean(p[c])}
                          disabled={locked}
                          aria-label={label}
                          onChange={() => toggle(p.event_key, c)}
                        />
                      </label>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex justify-end">
        <Button disabled={!dirty} loading={save.isPending} onClick={() => save.mutate()}>
          {tCommon("save")}
        </Button>
      </div>
    </div>
  );
}
