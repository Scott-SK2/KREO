import type { components } from "@kreo/api-client";
import { CalendarDays, MapPin, Sprout } from "lucide-react";
import { useTranslations } from "next-intl";
import type { ReactNode } from "react";

import { Badge, CompensationBadge, StatusBadge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { formatDate, requirementValue } from "@/lib/format";

type Role = components["schemas"]["Role"];

const LEVELS = ["beginner", "intermediate", "confirmed", "professional"] as const;
const REQUIREMENT_KEYS = [
  "playing_age_range",
  "languages",
  "skills",
  "voice_type",
  "instruments",
  "dance_styles",
  "costume_sizes",
  "driving_licence",
  "experience_level",
  "availability",
] as const;

type RequirementKey = (typeof REQUIREMENT_KEYS)[number];
const isRequirementKey = (k: string): k is RequirementKey =>
  (REQUIREMENT_KEYS as readonly string[]).includes(k);
const isLevel = (v: unknown): v is (typeof LEVELS)[number] =>
  typeof v === "string" && (LEVELS as readonly string[]).includes(v);

/** Carte d'un rôle : rémunération, détails, places, échéance, critères en mots simples, action. */
export function RoleCard({ role, action }: { role: Role; action?: ReactNode }) {
  const t = useTranslations();
  const slots = role.slots ?? 1;
  const left = Math.max(0, slots - role.accepted_count);
  const status = role.status ?? "open";
  const requirements = Object.entries((role.requirements as Record<string, unknown>) ?? {}).filter(
    ([, v]) => v !== null && v !== "" && !(Array.isArray(v) && v.length === 0),
  );

  return (
    <Card as="article" className="flex flex-col gap-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-xl normal-case tracking-normal">{role.title}</h3>
          {role.discipline ? (
            <p className="mt-1 text-sm text-taupe-dark">{role.discipline.label}</p>
          ) : null}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <CompensationBadge
            compensation={role.compensation}
            label={t(`compensation.${role.compensation}`)}
          />
          {status !== "open" ? (
            <StatusBadge status={status} label={t("opportunity.closed")} />
          ) : null}
        </div>
      </div>

      {role.compensation_details ? (
        <p className="text-sm text-brown">{role.compensation_details}</p>
      ) : null}
      {role.description ? <p className="text-sm text-brown">{role.description}</p> : null}

      <dl className="grid gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
        <div className="flex items-center gap-2 text-taupe-dark">
          <dt className="sr-only">{t("opportunity.slots", { count: slots })}</dt>
          <dd>
            {t("opportunity.slots", { count: slots })} ·{" "}
            {t("opportunity.slotsLeft", { count: left })}
          </dd>
        </div>
        <div className="flex items-center gap-2 text-taupe-dark">
          <CalendarDays aria-hidden="true" className="size-4" strokeWidth={1.5} />
          <dt className="sr-only">{t("discover.deadline")}</dt>
          <dd>
            {role.deadline_at
              ? t("opportunity.deadline", { date: formatDate(role.deadline_at) })
              : t("opportunity.noDeadline")}
          </dd>
        </div>
        {role.city?.label ? (
          <div className="flex items-center gap-2 text-taupe-dark">
            <MapPin aria-hidden="true" className="size-4" strokeWidth={1.5} />
            <dt className="sr-only">{t("discover.city")}</dt>
            <dd>{role.city.label}</dd>
          </div>
        ) : null}
      </dl>

      {requirements.length ? (
        <div>
          <h4 className="text-sm font-medium text-brown">{t("opportunity.requirements")}</h4>
          <ul className="mt-2 flex flex-wrap gap-2">
            {requirements.map(([key, value]) => {
              const label = isRequirementKey(key) ? t(`opportunity.requirementKeys.${key}`) : key;
              const display = isLevel(value)
                ? t(`profile.level.${value}`)
                : requirementValue(value);
              return (
                <li key={key}>
                  <Badge>
                    {label} : {display}
                  </Badge>
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-taupe/10 pt-4">
        <div>
          {role.beginner_friendly ? (
            <Badge tone="success">
              <Sprout aria-hidden="true" className="size-3.5" strokeWidth={1.5} />
              {t("opportunity.beginnerFriendly")}
            </Badge>
          ) : null}
        </div>
        {action}
      </div>
    </Card>
  );
}
