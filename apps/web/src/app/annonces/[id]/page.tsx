import { BadgeCheck, Clock3, MapPin } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";

import { ApplyDialog } from "@/components/opportunities/ApplyDialog";
import { RoleCard } from "@/components/opportunities/RoleCard";
import { ReportDialog } from "@/components/ReportDialog";
import { SafetyTips } from "@/components/SafetyTips";
import { Badge, StatusBadge } from "@/components/ui/Badge";
import { RingsPattern } from "@/components/ui/RingsPattern";
import { orNull, serverApi, unwrap } from "@/lib/api/server";
import { getCurrentUser } from "@/lib/auth";
import { formatDate } from "@/lib/format";
import { routes } from "@/lib/routes";

type Params = Promise<{ id: string }>;

async function loadOpportunity(id: string) {
  const api = await serverApi();
  return orNull(
    api
      .GET("/api/v1/opportunities/{opportunity_id}", { params: { path: { opportunity_id: id } } })
      .then(unwrap),
  );
}

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { id } = await params;
  const opportunity = await loadOpportunity(id);
  if (!opportunity) return {};
  const description = opportunity.description.slice(0, 160);
  return {
    title: `${opportunity.title} — ${opportunity.project.title}`,
    description,
    openGraph: { title: opportunity.title, description, type: "article" },
  };
}

export default async function OpportunityPage({ params }: { params: Params }) {
  const { id } = await params;
  const [opportunity, user, t] = await Promise.all([
    loadOpportunity(id),
    getCurrentUser(),
    getTranslations(),
  ]);
  if (!opportunity) notFound();

  const { project } = opportunity;
  const status = opportunity.status ?? "open";
  const isOpen = status === "open";

  return (
    <>
      <section className="relative overflow-hidden border-b border-taupe/10 bg-ivory/40">
        <RingsPattern className="absolute -top-48 -right-32 size-[34rem]" />
        <div className="kreo-container relative py-10">
          <p className="text-xs font-medium tracking-caps text-taupe-dark uppercase">
            {t("opportunity.project")} ·{" "}
            <Link
              href={routes.project(project.slug)}
              className="underline-offset-4 hover:underline"
            >
              {project.title}
            </Link>
          </p>
          <h1 className="mt-2 max-w-3xl text-3xl sm:text-4xl">{opportunity.title}</h1>
          <div className="mt-4 flex flex-wrap items-center gap-2">
            {!isOpen ? <StatusBadge status={status} label={t("opportunity.closed")} /> : null}
            {project.city?.label ? (
              <Badge>
                <MapPin aria-hidden="true" className="size-3.5" strokeWidth={1.5} />
                {project.city.label}
              </Badge>
            ) : null}
            {project.is_commercial ? <Badge>{t("opportunity.commercial")}</Badge> : null}
            {opportunity.created_by.is_verified ? (
              <Badge tone="gold">
                <BadgeCheck aria-hidden="true" className="size-3.5" strokeWidth={1.5} />
                {t("opportunity.verifiedOwner")}
              </Badge>
            ) : null}
          </div>
          <p className="mt-4 text-sm text-taupe-dark">
            {t("opportunity.by")}{" "}
            {opportunity.created_by.slug ? (
              <Link
                href={routes.profile(opportunity.created_by.slug)}
                className="font-medium text-brown underline-offset-4 hover:underline"
              >
                {opportunity.created_by.display_name}
              </Link>
            ) : (
              <span className="font-medium text-brown">{opportunity.created_by.display_name}</span>
            )}
            {opportunity.published_at ? ` · ${formatDate(opportunity.published_at)}` : ""}
          </p>
          {opportunity.owner_response_time_hours !== null ? (
            <p className="mt-2 inline-flex items-center gap-1 text-sm text-taupe-dark">
              <Clock3 aria-hidden="true" className="size-4" strokeWidth={1.5} />
              {t("opportunity.responseTime", {
                hours: Math.round(opportunity.owner_response_time_hours),
              })}
              <span className="text-xs">({t("opportunity.responseTimeNote")})</span>
            </p>
          ) : null}
        </div>
      </section>

      <div className="kreo-container grid gap-10 py-10 lg:grid-cols-[1fr_20rem]">
        <div className="flex flex-col gap-10">
          <section aria-labelledby="description">
            <h2 id="description" className="text-xl">
              {t("opportunity.description")}
            </h2>
            <div className="kreo-prose mt-3 whitespace-pre-line">{opportunity.description}</div>
            {opportunity.has_intimate_scene ? (
              <p className="mt-4 rounded-md border border-bordeaux/30 bg-bordeaux/5 p-3 text-sm text-bordeaux">
                {t("opportunity.intimateScene")}
              </p>
            ) : null}
          </section>

          <section aria-labelledby="roles">
            <h2 id="roles" className="text-xl">
              {t("opportunity.roles")}
            </h2>
            <div className="mt-4 flex flex-col gap-4">
              {opportunity.roles.map((role) => {
                const left = Math.max(0, (role.slots ?? 1) - role.accepted_count);
                const roleOpen = (role.status ?? "open") === "open" && isOpen && left > 0;
                return (
                  <RoleCard
                    key={role.id}
                    role={role}
                    action={
                      <ApplyDialog
                        roleId={role.id}
                        roleTitle={role.title}
                        opportunityId={opportunity.id}
                        myApplicationId={role.my_application_id}
                        isAuthenticated={Boolean(user)}
                        disabled={!roleOpen}
                      />
                    }
                  />
                );
              })}
            </div>
          </section>
        </div>

        <aside className="flex flex-col gap-6">
          <section className="rounded-xl border border-taupe/15 bg-white p-5">
            <h2 className="text-base normal-case tracking-normal">{t("opportunity.project")}</h2>
            <p className="mt-2 font-medium text-brown">{project.title}</p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {project.disciplines.map((d) => (
                <Badge key={d.id}>{d.label}</Badge>
              ))}
            </div>
            {project.starts_on ? (
              <p className="mt-3 text-sm text-taupe-dark">
                {project.ends_on
                  ? t("project.dates", {
                      start: formatDate(project.starts_on),
                      end: formatDate(project.ends_on),
                    })
                  : t("project.from", { start: formatDate(project.starts_on) })}
              </p>
            ) : null}
            <Link
              href={routes.project(project.slug)}
              className="mt-4 inline-flex min-h-touch items-center text-sm font-medium text-taupe-dark underline-offset-4 hover:underline"
            >
              {t("opportunity.seeProject")}
            </Link>
          </section>
          <SafetyTips tips={opportunity.safety_tips} />
          {project.is_commercial ? null : (
            <p className="text-xs text-taupe-dark">{t("opportunity.volunteerRules")}</p>
          )}
          <div>
            <ReportDialog
              targetType="opportunity"
              targetId={opportunity.id}
              isAuthenticated={Boolean(user)}
              returnTo={routes.opportunity(opportunity.id)}
              label={t("opportunity.report")}
            />
          </div>
        </aside>
      </div>
    </>
  );
}
