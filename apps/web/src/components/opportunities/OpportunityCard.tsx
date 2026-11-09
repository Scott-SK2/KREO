import type { components } from "@kreo/api-client";
import { BadgeCheck, CalendarDays, MapPin, Sprout } from "lucide-react";
import Link from "next/link";
import { useTranslations } from "next-intl";

import { Badge, CompensationBadge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { formatDate } from "@/lib/format";
import { routes } from "@/lib/routes";

export type OpportunityListItem = components["schemas"]["OpportunityList"];

/** Échéance la plus proche parmi les rôles ouverts. */
export function nearestDeadline(roles: components["schemas"]["Role"][]): string | null {
  const dates = roles
    .map((r) => r.deadline_at)
    .filter((d): d is string => Boolean(d))
    .sort();
  return dates[0] ?? null;
}

/**
 * Carte d'annonce : titre, projet, commune, rôles avec rémunération et places
 * restantes, échéance, mentions débutants et porteur vérifié.
 */
export function OpportunityCard({ opportunity }: { opportunity: OpportunityListItem }) {
  const t = useTranslations();
  const { project, roles } = opportunity;
  const deadline = nearestDeadline(roles);
  const beginnerFriendly = roles.some((r) => r.beginner_friendly);
  const cityLabel = project.city?.label;

  return (
    <Card as="article" interactive className="flex h-full flex-col gap-4">
      <div className="flex flex-col gap-1">
        <p className="text-xs font-medium tracking-caps text-taupe-dark uppercase">
          {project.title}
        </p>
        <h3 className="text-lg leading-snug normal-case tracking-normal">
          <Link
            href={routes.opportunity(opportunity.id)}
            className="after:absolute after:inset-0 after:rounded-xl focus-visible:outline-none"
          >
            {opportunity.title}
          </Link>
        </h3>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-taupe-dark">
          {cityLabel ? (
            <span className="inline-flex items-center gap-1">
              <MapPin aria-hidden="true" className="size-4" strokeWidth={1.5} />
              {cityLabel}
            </span>
          ) : null}
          <span className="inline-flex items-center gap-1">
            <CalendarDays aria-hidden="true" className="size-4" strokeWidth={1.5} />
            {deadline
              ? t("opportunity.deadline", { date: formatDate(deadline) })
              : t("opportunity.noDeadline")}
          </span>
        </div>
      </div>

      <ul className="flex flex-col gap-2" aria-label={t("opportunity.roles")}>
        {roles.slice(0, 3).map((role) => {
          const left = Math.max(0, (role.slots ?? 1) - role.accepted_count);
          return (
            <li
              key={role.id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-md bg-ivory/60 px-3 py-2 text-sm"
            >
              <span className="font-medium text-brown">{role.title}</span>
              <span className="flex items-center gap-2">
                <CompensationBadge
                  compensation={role.compensation}
                  label={t(`compensation.${role.compensation}`)}
                />
                <span className="text-xs text-taupe-dark">
                  {t("opportunity.slotsLeft", { count: left })}
                </span>
              </span>
            </li>
          );
        })}
        {roles.length > 3 ? (
          <li className="text-xs text-taupe-dark">+{roles.length - 3}</li>
        ) : null}
      </ul>

      <div className="mt-auto flex flex-wrap items-center gap-2">
        {beginnerFriendly ? (
          <Badge tone="success">
            <Sprout aria-hidden="true" className="size-3.5" strokeWidth={1.5} />
            {t("opportunity.beginnerFriendly")}
          </Badge>
        ) : null}
        {project.owner.is_verified ? (
          <Badge tone="gold">
            <BadgeCheck aria-hidden="true" className="size-3.5" strokeWidth={1.5} />
            {t("opportunity.verifiedOwner")}
          </Badge>
        ) : null}
        {project.is_commercial ? <Badge>{t("opportunity.commercial")}</Badge> : null}
      </div>
    </Card>
  );
}
