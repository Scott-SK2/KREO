import { ArrowLeft } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";

import { ApplicationActions } from "@/components/applications/ApplicationActions";
import { PageHeader } from "@/components/PageHeader";
import { Badge, CompensationBadge, StatusBadge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { orNull, serverApi, unwrap } from "@/lib/api/server";
import { formatDateTime } from "@/lib/format";
import { routes } from "@/lib/routes";

type Params = Promise<{ id: string }>;

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("application");
  return { title: t("detailTitle"), robots: { index: false } };
}

export default async function ApplicationDetailPage({ params }: { params: Params }) {
  const { id } = await params;
  const api = await serverApi();
  const [t, application, events] = await Promise.all([
    getTranslations(),
    orNull(
      api
        .GET("/api/v1/applications/{application_id}", { params: { path: { application_id: id } } })
        .then(unwrap),
    ),
    orNull(
      api
        .GET("/api/v1/applications/{application_id}/events", {
          params: { path: { application_id: id } },
        })
        .then(unwrap),
    ),
  ]);
  if (!application) notFound();

  const status = application.status ?? "submitted";
  const timeline = [...(events ?? [])].sort((a, b) => b.created_at.localeCompare(a.created_at));

  return (
    <>
      <PageHeader
        eyebrow={
          <Link
            href={routes.applications}
            className="inline-flex items-center gap-1 hover:underline"
          >
            <ArrowLeft aria-hidden="true" className="size-3.5" strokeWidth={1.5} />
            {t("nav.myApplications")}
          </Link>
        }
        title={application.role.title}
        lead={`${application.opportunity_title} · ${application.project_title}`}
        actions={<StatusBadge status={status} label={t(`application.status.${status}`)} />}
      />
      <div className="kreo-container grid gap-6 py-10 lg:grid-cols-[1fr_22rem]">
        <div className="flex flex-col gap-6">
          <Card as="section" aria-labelledby="ma-candidature">
            <h2 id="ma-candidature" className="text-base normal-case tracking-normal">
              {t("application.detailTitle")}
            </h2>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <CompensationBadge
                compensation={application.role.compensation}
                label={t(`compensation.${application.role.compensation}`)}
              />
              {application.availability_confirmed ? (
                <Badge tone="success">{t("application.availabilityConfirmed")}</Badge>
              ) : null}
              <span className="text-xs text-taupe-dark">
                {t("application.submittedOn", { date: formatDateTime(application.submitted_at) })}
              </span>
            </div>
            <h3 className="mt-5 text-sm font-medium text-brown normal-case tracking-normal">
              {t("application.yourMessage")}
            </h3>
            <p className="mt-1 text-sm whitespace-pre-line text-brown">
              {application.message || (
                <span className="text-taupe-dark">{t("application.noMessage")}</span>
              )}
            </p>
            <div className="mt-6 border-t border-taupe/10 pt-5">
              <ApplicationActions
                applicationId={application.id}
                allowedTransitions={application.allowed_transitions}
                conversationId={application.conversation_id}
              />
            </div>
          </Card>
          <Link
            href={routes.opportunity(application.role.opportunity_id)}
            className="inline-flex min-h-touch items-center text-sm font-medium text-taupe-dark underline-offset-4 hover:underline"
          >
            {t("application.seeOpportunity")}
          </Link>
        </div>

        <Card as="section" aria-labelledby="historique">
          <h2 id="historique" className="text-base normal-case tracking-normal">
            {t("application.history")}
          </h2>
          {timeline.length ? (
            <ol className="mt-4 flex flex-col">
              {timeline.map((event, index) => (
                <li key={event.id} className="relative flex gap-3 pb-5 last:pb-0">
                  <span className="flex flex-col items-center">
                    <span
                      aria-hidden="true"
                      className={`mt-1 size-2.5 rounded-full ${index === 0 ? "bg-gold" : "bg-taupe/40"}`}
                    />
                    {index < timeline.length - 1 ? (
                      <span aria-hidden="true" className="mt-1 w-px flex-1 bg-taupe/20" />
                    ) : null}
                  </span>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-brown">
                      {t(`application.status.${event.to_status}`)}
                    </p>
                    <p className="text-xs text-taupe-dark">
                      {formatDateTime(event.created_at)} · {event.actor.display_name}
                    </p>
                    {event.note ? (
                      <p className="mt-1 text-sm whitespace-pre-line text-brown">{event.note}</p>
                    ) : null}
                  </div>
                </li>
              ))}
            </ol>
          ) : (
            <p className="mt-3 text-sm text-taupe-dark">{t("application.noMessage")}</p>
          )}
        </Card>
      </div>
    </>
  );
}
