import { BadgeCheck, ExternalLink, MapPin, Sprout } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";

import { Avatar } from "@/components/ui/Avatar";
import { Badge } from "@/components/ui/Badge";
import { RingsPattern } from "@/components/ui/RingsPattern";
import { orNull, serverApi, unwrap } from "@/lib/api/server";
import { formatDate } from "@/lib/format";
import { routes } from "@/lib/routes";

type Params = Promise<{ slug: string }>;

const LEVELS = ["beginner", "intermediate", "confirmed", "professional"] as const;
type Level = (typeof LEVELS)[number];
const isLevel = (v: unknown): v is Level =>
  typeof v === "string" && (LEVELS as readonly string[]).includes(v);

interface LinkItem {
  url: string;
  label: string;
}

/** Normalise `video_links` / `external_links` (chaînes ou objets {url,label}). */
function toLinks(value: unknown): LinkItem[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item): LinkItem | null => {
      if (typeof item === "string") return { url: item, label: item };
      if (item && typeof item === "object" && typeof (item as { url?: unknown }).url === "string") {
        const { url, label, title } = item as { url: string; label?: string; title?: string };
        return { url, label: label ?? title ?? url };
      }
      return null;
    })
    .filter((l): l is LinkItem => l !== null && /^https?:\/\//.test(l.url));
}

function toGallery(value: unknown): { id: string; url: string; alt: string }[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item, index) => {
      if (typeof item === "string") return { id: String(index), url: item, alt: "" };
      if (item && typeof item === "object" && typeof (item as { url?: unknown }).url === "string") {
        const { id, url, alt } = item as { id?: string; url: string; alt?: string };
        return { id: id ?? String(index), url, alt: alt ?? "" };
      }
      return null;
    })
    .filter((g): g is { id: string; url: string; alt: string } => g !== null);
}

async function loadProfile(slug: string) {
  const api = await serverApi();
  return orNull(api.GET("/api/v1/profiles/{slug}", { params: { path: { slug } } }).then(unwrap));
}

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { slug } = await params;
  const profile = await loadProfile(slug);
  if (!profile) return {};
  return { title: profile.display_name, description: profile.bio?.slice(0, 160) };
}

export default async function ProfilePage({ params }: { params: Params }) {
  const { slug } = await params;
  const profile = await loadProfile(slug);
  if (!profile) notFound();

  const api = await serverApi();
  const [t, credits] = await Promise.all([
    getTranslations(),
    orNull(api.GET("/api/v1/profiles/{slug}/credits", { params: { path: { slug } } }).then(unwrap)),
  ]);

  const videos = toLinks(profile.video_links);
  const links = toLinks(profile.external_links);
  const gallery = toGallery(profile.gallery);

  return (
    <>
      <section className="relative overflow-hidden border-b border-taupe/10 bg-ivory/40">
        <RingsPattern className="absolute -top-40 -right-24 size-[30rem]" rings={11} />
        <div className="kreo-container relative flex flex-col gap-6 py-12 sm:flex-row sm:items-center">
          <Avatar name={profile.display_name} src={profile.avatar?.url} size="xl" />
          <div>
            <h1 className="text-3xl sm:text-4xl">{profile.display_name}</h1>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              {profile.disciplines.map((d) => (
                <Badge key={d.id}>{d.label}</Badge>
              ))}
              {profile.is_verified_owner ? (
                <Badge tone="gold">
                  <BadgeCheck aria-hidden="true" className="size-3.5" strokeWidth={1.5} />
                  {t("profile.verifiedOwner")}
                </Badge>
              ) : null}
              {profile.open_to_beginner_roles ? (
                <Badge tone="success">
                  <Sprout aria-hidden="true" className="size-3.5" strokeWidth={1.5} />
                  {t("profile.openToBeginners")}
                </Badge>
              ) : null}
            </div>
            <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-sm text-taupe-dark">
              {profile.city?.label ? (
                <span className="inline-flex items-center gap-1">
                  <MapPin aria-hidden="true" className="size-4" strokeWidth={1.5} />
                  {profile.city.label}
                </span>
              ) : null}
              {isLevel(profile.experience_level) ? (
                <span>
                  {t("profile.experience")} : {t(`profile.level.${profile.experience_level}`)}
                </span>
              ) : null}
              <span>{t("profile.memberSince", { date: formatDate(profile.created_at) })}</span>
            </div>
          </div>
        </div>
      </section>

      <div className="kreo-container grid gap-10 py-10 lg:grid-cols-[1fr_20rem]">
        <div className="flex flex-col gap-10">
          {profile.bio ? (
            <section aria-labelledby="bio">
              <h2 id="bio" className="text-xl">
                {t("profile.bio")}
              </h2>
              <div className="kreo-prose mt-3 whitespace-pre-line">{profile.bio}</div>
            </section>
          ) : null}

          {gallery.length ? (
            <section aria-labelledby="galerie">
              <h2 id="galerie" className="text-xl">
                {t("profile.gallery")}
              </h2>
              <ul className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
                {gallery.map((g) => (
                  <li key={g.id} className="overflow-hidden rounded-lg bg-ivory">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={g.url} alt={g.alt} className="aspect-square size-full object-cover" />
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          <section aria-labelledby="credits">
            <h2 id="credits" className="text-xl">
              {t("profile.credits")}
            </h2>
            {credits?.length ? (
              <ul className="mt-4 flex flex-col gap-2">
                {credits.map((c) => (
                  <li
                    key={c.id}
                    className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-gold/40 bg-gold/10 px-4 py-3 text-sm"
                  >
                    <span>
                      <span className="font-medium text-brown">{c.role_name}</span>
                      <span className="text-taupe-dark"> · </span>
                      <Link
                        href={routes.project(c.project_slug)}
                        className="text-brown underline-offset-4 hover:underline"
                      >
                        {c.project_title}
                      </Link>
                    </span>
                    {c.confirmed_at ? (
                      <span className="text-xs text-taupe-dark">{formatDate(c.confirmed_at)}</span>
                    ) : null}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 text-sm text-taupe-dark">{t("profile.noCredits")}</p>
            )}
            <p className="mt-3 text-xs text-taupe-dark">{t("credits.note")}</p>
          </section>
        </div>

        <aside className="flex flex-col gap-8">
          {videos.length ? (
            <section aria-labelledby="videos">
              <h2 id="videos" className="text-base normal-case tracking-normal">
                {t("profile.videos")}
              </h2>
              <ul className="mt-3 flex flex-col gap-1">
                {videos.map((v) => (
                  <li key={v.url}>
                    <a
                      href={v.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex min-h-touch items-center gap-2 text-sm text-brown underline-offset-4 hover:underline"
                    >
                      <ExternalLink
                        aria-hidden="true"
                        className="size-4 shrink-0"
                        strokeWidth={1.5}
                      />
                      <span className="break-all">{v.label}</span>
                      <span className="sr-only">({t("common.newTab")})</span>
                    </a>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
          {links.length ? (
            <section aria-labelledby="liens">
              <h2 id="liens" className="text-base normal-case tracking-normal">
                {t("profile.links")}
              </h2>
              <ul className="mt-3 flex flex-col gap-1">
                {links.map((l) => (
                  <li key={l.url}>
                    <a
                      href={l.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex min-h-touch items-center gap-2 text-sm text-brown underline-offset-4 hover:underline"
                    >
                      <ExternalLink
                        aria-hidden="true"
                        className="size-4 shrink-0"
                        strokeWidth={1.5}
                      />
                      <span className="break-all">{l.label}</span>
                      <span className="sr-only">({t("common.newTab")})</span>
                    </a>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
        </aside>
      </div>
    </>
  );
}
