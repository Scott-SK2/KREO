import { Bell, Compass, Mail, Send, UserRound } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { getTranslations } from "next-intl/server";

import { CompletionMeter } from "@/components/dashboard/CompletionMeter";
import { InvitationsList } from "@/components/dashboard/InvitationsList";
import { PhoneVerification } from "@/components/dashboard/PhoneVerification";
import { PageHeader } from "@/components/PageHeader";
import { ProjectCard } from "@/components/projects/ProjectCard";
import { Badge, StatusBadge } from "@/components/ui/Badge";
import { ButtonLink } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { orNull, serverApi, unwrap } from "@/lib/api/server";
import { getCurrentUser } from "@/lib/auth";
import { formatDate } from "@/lib/format";
import { routes } from "@/lib/routes";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("dashboard");
  return { title: t("title"), robots: { index: false } };
}

export default async function DashboardPage() {
  const user = await getCurrentUser();
  if (!user) redirect(routes.login(routes.dashboard));

  const api = await serverApi();
  const [t, profile, invitations, applications, projects] = await Promise.all([
    getTranslations(),
    orNull(api.GET("/api/v1/me/profile").then(unwrap)),
    orNull(api.GET("/api/v1/me/invitations").then(unwrap)),
    orNull(
      api.GET("/api/v1/me/applications", { params: { query: { page_size: 5 } } }).then(unwrap),
    ),
    orNull(
      api.GET("/api/v1/projects", { params: { query: { mine: true, page_size: 6 } } }).then(unwrap),
    ),
  ]);

  const completion = (profile?.completion ?? {}) as { score?: number; missing?: string[] };
  const name = profile?.display_name || user.email.split("@")[0] || "";
  const quickLinks = [
    { href: routes.discover, label: t("nav.discover"), icon: Compass },
    { href: routes.applications, label: t("nav.myApplications"), icon: Send },
    { href: routes.messages, label: t("nav.messages"), icon: Mail },
    { href: routes.notifications, label: t("nav.notifications"), icon: Bell },
    { href: routes.account, label: t("nav.account"), icon: UserRound },
  ];

  return (
    <>
      <PageHeader
        eyebrow={t("dashboard.title")}
        title={t("dashboard.welcome", { name })}
        actions={
          user.profile_slug ? (
            <ButtonLink href={routes.profile(user.profile_slug)} variant="secondary" size="sm">
              {t("profile.title")}
            </ButtonLink>
          ) : null
        }
      />
      <div className="kreo-container grid gap-6 py-10 lg:grid-cols-[1fr_22rem]">
        <div className="flex flex-col gap-6">
          <Card as="section" aria-labelledby="completion">
            <h2 id="completion" className="text-base normal-case tracking-normal">
              {t("dashboard.completeProfile")}
            </h2>
            <div className="mt-4">
              <CompletionMeter score={completion.score ?? 0} missing={completion.missing ?? []} />
            </div>
          </Card>

          {!user.phone_verified ? (
            <Card as="section" aria-labelledby="telephone" className="border-gold/40">
              <h2 id="telephone" className="text-base normal-case tracking-normal">
                {t("dashboard.phone.title")}
              </h2>
              <div className="mt-4">
                <PhoneVerification />
              </div>
            </Card>
          ) : null}

          <Card as="section" aria-labelledby="candidatures">
            <div className="flex items-center justify-between gap-3">
              <h2 id="candidatures" className="text-base normal-case tracking-normal">
                {t("dashboard.myApplications")}
              </h2>
              <Link
                href={routes.applications}
                className="inline-flex min-h-touch items-center text-sm text-taupe-dark underline-offset-4 hover:underline"
              >
                {t("dashboard.seeApplications")}
              </Link>
            </div>
            {applications?.results.length ? (
              <ul className="mt-4 divide-y divide-taupe/10">
                {applications.results.map((a) => {
                  const status = a.status ?? "submitted";
                  return (
                    <li key={a.id}>
                      <Link
                        href={routes.application(a.id)}
                        className="flex min-h-touch flex-wrap items-center justify-between gap-2 py-3 hover:bg-ivory/50"
                      >
                        <span className="min-w-0">
                          <span className="block truncate text-sm font-medium text-brown">
                            {a.role.title} · {a.project_title}
                          </span>
                          <span className="block text-xs text-taupe-dark">
                            {t("application.submittedOn", { date: formatDate(a.submitted_at) })}
                          </span>
                        </span>
                        <StatusBadge status={status} label={t(`application.status.${status}`)} />
                      </Link>
                    </li>
                  );
                })}
              </ul>
            ) : (
              <p className="mt-3 text-sm text-taupe-dark">{t("dashboard.noApplications")}</p>
            )}
          </Card>

          <section aria-labelledby="mes-projets">
            <h2 id="mes-projets" className="text-xl">
              {t("dashboard.myProjects")}
            </h2>
            {projects?.results.length ? (
              <ul className="mt-4 grid gap-4 sm:grid-cols-2">
                {projects.results.map((p) => (
                  <li key={p.id} className="relative">
                    <ProjectCard project={p} />
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 text-sm text-taupe-dark">{t("dashboard.noProjects")}</p>
            )}
          </section>
        </div>

        <aside className="flex flex-col gap-6">
          <Card as="section" aria-labelledby="acces">
            <h2 id="acces" className="text-base normal-case tracking-normal">
              {t("dashboard.quickLinks")}
            </h2>
            <ul className="mt-3 flex flex-col">
              {quickLinks.map(({ href, label, icon: Icon }) => (
                <li key={href}>
                  <Link
                    href={href}
                    className="flex min-h-touch items-center gap-3 rounded-md px-2 text-sm text-brown hover:bg-ivory"
                  >
                    <Icon aria-hidden="true" className="size-4 text-taupe-dark" strokeWidth={1.5} />
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </Card>
          <Card as="section" aria-labelledby="invitations">
            <div className="flex items-center justify-between gap-2">
              <h2 id="invitations" className="text-base normal-case tracking-normal">
                {t("dashboard.invitations")}
              </h2>
              {user.phone_verified ? (
                <Badge tone="success">{t("dashboard.phone.verified")}</Badge>
              ) : null}
            </div>
            <div className="mt-4">
              <InvitationsList invitations={invitations ?? []} left={user.invitations_left} />
            </div>
          </Card>
        </aside>
      </div>
    </>
  );
}
