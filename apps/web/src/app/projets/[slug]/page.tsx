import { BadgeCheck, CalendarDays, MapPin } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";

import { OpportunityCard } from "@/components/opportunities/OpportunityCard";
import { Avatar } from "@/components/ui/Avatar";
import { Badge, StatusBadge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { RingsPattern } from "@/components/ui/RingsPattern";
import { orNull, serverApi, unwrap } from "@/lib/api/server";
import { formatDate, formatDateTime } from "@/lib/format";
import { routes } from "@/lib/routes";

type Params = Promise<{ slug: string }>;

async function loadProject(slug: string) {
  const api = await serverApi();
  return orNull(
    api
      .GET("/api/v1/projects/{project_id}", { params: { path: { project_id: slug } } })
      .then(unwrap),
  );
}

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { slug } = await params;
  const project = await loadProject(slug);
  if (!project) return {};
  const description = project.description.slice(0, 160);
  return { title: project.title, description, openGraph: { title: project.title, description } };
}

export default async function ProjectPage({ params }: { params: Params }) {
  const { slug } = await params;
  const project = await loadProject(slug);
  if (!project) notFound();

  const api = await serverApi();
  const [t, updates, credits, opportunities] = await Promise.all([
    getTranslations(),
    orNull(
      api
        .GET("/api/v1/projects/{project_id}/updates", {
          params: { path: { project_id: project.id } },
        })
        .then(unwrap),
    ),
    orNull(
      api
        .GET("/api/v1/projects/{project_id}/credits", {
          params: { path: { project_id: project.id } },
        })
        .then(unwrap),
    ),
    orNull(
      api
        .GET("/api/v1/projects/{project_id}/opportunities", {
          params: { path: { project_id: project.id } },
        })
        .then(unwrap),
    ),
  ]);

  const status = project.status ?? "active";
  const confirmedCredits = (credits ?? []).filter(
    (c) => c.status === undefined || c.status === "confirmed",
  );
  const openOpportunities = (opportunities ?? []).filter((o) => (o.status ?? "open") === "open");
  const roleLabel: Record<string, string> = {
    owner: t("project.owner"),
    manager: t("project.coorganiser"),
    member: t("project.member"),
  };

  return (
    <>
      <section className="relative overflow-hidden border-b border-taupe/10 bg-ivory/50">
        {project.cover?.url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={project.cover.url}
            alt=""
            className="absolute inset-0 size-full object-cover opacity-30"
          />
        ) : (
          <RingsPattern className="absolute -top-56 -right-32 size-[40rem]" rings={14} />
        )}
        <div className="kreo-container relative py-12">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={status} label={t(`project.status.${status}`)} />
            {project.is_commercial ? <Badge>{t("opportunity.commercial")}</Badge> : null}
            {project.disciplines.map((d) => (
              <Badge key={d.id} tone="neutral">
                {d.label}
              </Badge>
            ))}
          </div>
          <h1 className="mt-4 max-w-3xl text-3xl sm:text-5xl">{project.title}</h1>
          <div className="mt-5 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-taupe-dark">
            <span className="inline-flex items-center gap-2">
              <Avatar name={project.owner.display_name} size="sm" />
              {t("project.owner")} :{" "}
              {project.owner.slug ? (
                <Link
                  href={routes.profile(project.owner.slug)}
                  className="font-medium text-brown underline-offset-4 hover:underline"
                >
                  {project.owner.display_name}
                </Link>
              ) : (
                <span className="font-medium text-brown">{project.owner.display_name}</span>
              )}
              {project.owner.is_verified ? (
                <BadgeCheck aria-hidden="true" className="size-4 text-gold" strokeWidth={1.5} />
              ) : null}
            </span>
            {project.city?.label ? (
              <span className="inline-flex items-center gap-1">
                <MapPin aria-hidden="true" className="size-4" strokeWidth={1.5} />
                {project.city.label}
              </span>
            ) : null}
            {project.starts_on || project.ends_on ? (
              <span className="inline-flex items-center gap-1">
                <CalendarDays aria-hidden="true" className="size-4" strokeWidth={1.5} />
                {project.starts_on && project.ends_on
                  ? t("project.dates", {
                      start: formatDate(project.starts_on),
                      end: formatDate(project.ends_on),
                    })
                  : project.starts_on
                    ? t("project.from", { start: formatDate(project.starts_on) })
                    : t("project.until", { end: formatDate(project.ends_on) })}
              </span>
            ) : null}
          </div>
        </div>
      </section>

      <div className="kreo-container grid gap-10 py-10 lg:grid-cols-[1fr_20rem]">
        <div className="flex flex-col gap-10">
          <section aria-labelledby="apropos">
            <h2 id="apropos" className="text-xl">
              {t("project.about")}
            </h2>
            <div className="kreo-prose mt-3 whitespace-pre-line">{project.description}</div>
          </section>

          <section aria-labelledby="roles-ouverts">
            <h2 id="roles-ouverts" className="text-xl">
              {t("project.openRoles")}
            </h2>
            {openOpportunities.length ? (
              <ul className="mt-4 grid gap-4 sm:grid-cols-2">
                {openOpportunities.map((o) => (
                  <li key={o.id} className="relative">
                    <OpportunityCard opportunity={o} />
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 text-sm text-taupe-dark">{t("project.noOpenRoles")}</p>
            )}
          </section>

          <section aria-labelledby="actualites">
            <h2 id="actualites" className="text-xl">
              {t("project.updates")}
            </h2>
            {updates?.length ? (
              <ol className="mt-4 flex flex-col gap-4">
                {updates.map((u) => (
                  <li key={u.id}>
                    <Card padding="sm">
                      <p className="text-xs text-taupe-dark">
                        {u.author.display_name} · {formatDateTime(u.created_at)}
                      </p>
                      <p className="mt-2 text-sm whitespace-pre-line text-brown">{u.body}</p>
                    </Card>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="mt-3 text-sm text-taupe-dark">{t("project.noUpdates")}</p>
            )}
          </section>
        </div>

        <aside className="flex flex-col gap-8">
          <section aria-labelledby="equipe">
            <h2 id="equipe" className="text-base normal-case tracking-normal">
              {t("project.team")} · {t("project.members", { count: project.members.length })}
            </h2>
            <ul className="mt-3 flex flex-col gap-3">
              {project.members.map((m) => (
                <li key={m.user_id} className="flex items-center gap-3">
                  <Avatar name={m.user.display_name} size="sm" />
                  <div className="min-w-0">
                    {m.user.slug ? (
                      <Link
                        href={routes.profile(m.user.slug)}
                        className="block truncate text-sm font-medium text-brown underline-offset-4 hover:underline"
                      >
                        {m.user.display_name}
                      </Link>
                    ) : (
                      <span className="block truncate text-sm font-medium text-brown">
                        {m.user.display_name}
                      </span>
                    )}
                    <p className="text-xs text-taupe-dark">
                      {m.role_title || roleLabel[m.role] || m.role}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          </section>

          <section aria-labelledby="credits">
            <h2 id="credits" className="text-base normal-case tracking-normal">
              {t("project.credits")}
            </h2>
            {confirmedCredits.length ? (
              <ul className="mt-3 flex flex-col gap-2">
                {confirmedCredits.map((c) => (
                  <li
                    key={c.id}
                    className="flex items-center justify-between gap-3 rounded-md border border-gold/40 bg-gold/10 px-3 py-2 text-sm"
                  >
                    <span className="font-medium text-brown">{c.user.display_name}</span>
                    <span className="text-taupe-dark">{c.role_name}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 text-sm text-taupe-dark">{t("project.noCredits")}</p>
            )}
            <p className="mt-3 text-xs text-taupe-dark">{t("credits.note")}</p>
          </section>
        </aside>
      </div>
    </>
  );
}
