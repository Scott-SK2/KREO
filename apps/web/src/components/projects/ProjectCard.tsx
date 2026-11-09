import type { components } from "@kreo/api-client";
import { MapPin } from "lucide-react";
import Link from "next/link";
import { useTranslations } from "next-intl";

import { Badge, StatusBadge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { RingsPattern } from "@/components/ui/RingsPattern";
import { formatDate } from "@/lib/format";
import { routes } from "@/lib/routes";

export type ProjectListItem = components["schemas"]["ProjectList"];

/** Carte projet : couverture (ou ondes), statut, disciplines, porteur, dates. */
export function ProjectCard({ project }: { project: ProjectListItem }) {
  const t = useTranslations();
  const status = project.status ?? "active";
  return (
    <Card as="article" interactive padding="none" className="flex h-full flex-col overflow-hidden">
      <div className="relative h-28 overflow-hidden bg-ivory">
        {project.cover?.url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={project.cover.url} alt="" className="size-full object-cover" />
        ) : (
          <RingsPattern className="absolute -top-24 -right-10 size-72" rings={10} />
        )}
        <div className="absolute top-3 left-3">
          <StatusBadge status={status} label={t(`project.status.${status}`)} />
        </div>
      </div>
      <div className="flex flex-1 flex-col gap-3 p-5">
        <h3 className="text-lg leading-snug normal-case tracking-normal">
          <Link
            href={routes.project(project.slug)}
            className="after:absolute after:inset-0 after:rounded-xl focus-visible:outline-none"
          >
            {project.title}
          </Link>
        </h3>
        <div className="flex flex-wrap gap-1.5">
          {project.disciplines.map((d) => (
            <Badge key={d.id}>{d.label}</Badge>
          ))}
        </div>
        <div className="mt-auto flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-taupe-dark">
          <span>
            {t("project.owner")} : {project.owner.display_name}
          </span>
          {project.city?.label ? (
            <span className="inline-flex items-center gap-1">
              <MapPin aria-hidden="true" className="size-4" strokeWidth={1.5} />
              {project.city.label}
            </span>
          ) : null}
          {project.starts_on ? (
            <span>
              {project.ends_on
                ? t("project.dates", {
                    start: formatDate(project.starts_on),
                    end: formatDate(project.ends_on),
                  })
                : t("project.from", { start: formatDate(project.starts_on) })}
            </span>
          ) : null}
        </div>
      </div>
    </Card>
  );
}
