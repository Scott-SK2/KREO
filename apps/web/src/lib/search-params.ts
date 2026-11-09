/**
 * Filtres de la page Découverte, reflétés dans l'URL pour être partageables.
 * `parse` tolère les valeurs inconnues ; `serialize` omet les valeurs par défaut.
 */

export const COMPENSATIONS = ["paid", "volunteer", "expenses", "negotiable"] as const;
export type Compensation = (typeof COMPENSATIONS)[number];

export const SORTS = ["recent", "relevance"] as const;
export type Sort = (typeof SORTS)[number];

export const TABS = ["annonces", "projets", "createurs"] as const;
export type DiscoverTab = (typeof TABS)[number];

export interface OpportunityFilters {
  q: string;
  disciplines: string[];
  city: number | null;
  compensation: Compensation[];
  beginnerFriendly: boolean;
  sort: Sort;
}

export const DEFAULT_FILTERS: OpportunityFilters = {
  q: "",
  disciplines: [],
  city: null,
  compensation: [],
  beginnerFriendly: false,
  sort: "recent",
};

type ParamsLike = URLSearchParams | Record<string, string | string[] | undefined>;

function read(params: ParamsLike, key: string): string | null {
  if (params instanceof URLSearchParams) return params.get(key);
  const value = params[key];
  if (Array.isArray(value)) return value[0] ?? null;
  return value ?? null;
}

function splitList(value: string | null): string[] {
  if (!value) return [];
  return Array.from(
    new Set(
      value
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
    ),
  );
}

export function parseTab(params: ParamsLike): DiscoverTab {
  const value = read(params, "onglet");
  return (TABS as readonly string[]).includes(value ?? "") ? (value as DiscoverTab) : "annonces";
}

export function parseFilters(params: ParamsLike): OpportunityFilters {
  const cityRaw = read(params, "commune");
  const city = cityRaw && /^\d+$/.test(cityRaw) ? Number(cityRaw) : null;
  const sortRaw = read(params, "tri");
  const sort = (SORTS as readonly string[]).includes(sortRaw ?? "") ? (sortRaw as Sort) : "recent";
  const compensation = splitList(read(params, "remuneration")).filter((c): c is Compensation =>
    (COMPENSATIONS as readonly string[]).includes(c),
  );
  return {
    q: (read(params, "q") ?? "").trim(),
    disciplines: splitList(read(params, "discipline")),
    city,
    compensation,
    beginnerFriendly: read(params, "debutants") === "1",
    sort,
  };
}

/** Sérialise les filtres (et l'onglet) en query string, sans `?` ni valeurs par défaut. */
export function serializeFilters(
  filters: Partial<OpportunityFilters>,
  tab: DiscoverTab = "annonces",
): string {
  const params = new URLSearchParams();
  if (tab !== "annonces") params.set("onglet", tab);
  const f = { ...DEFAULT_FILTERS, ...filters };
  if (f.q.trim()) params.set("q", f.q.trim());
  if (f.disciplines.length) params.set("discipline", f.disciplines.join(","));
  if (f.city !== null) params.set("commune", String(f.city));
  if (f.compensation.length) params.set("remuneration", f.compensation.join(","));
  if (f.beginnerFriendly) params.set("debutants", "1");
  if (f.sort !== "recent") params.set("tri", f.sort);
  return params.toString();
}

/** Nombre de filtres actifs (hors tri et recherche textuelle). */
export function countActiveFilters(f: OpportunityFilters): number {
  return (
    (f.disciplines.length ? 1 : 0) +
    (f.city !== null ? 1 : 0) +
    (f.compensation.length ? 1 : 0) +
    (f.beginnerFriendly ? 1 : 0)
  );
}

/** Paramètres de requête attendus par GET /opportunities. */
export function toOpportunityQuery(f: OpportunityFilters) {
  return {
    q: f.q || undefined,
    discipline: f.disciplines.length ? f.disciplines.join(",") : undefined,
    city: f.city !== null ? String(f.city) : undefined,
    compensation: f.compensation.length ? f.compensation.join(",") : undefined,
    beginner_friendly: f.beginnerFriendly ? true : undefined,
    sort: f.sort !== "recent" ? f.sort : undefined,
  };
}

/** Extrait le `cursor` d'une URL `next` renvoyée par l'API. */
export function cursorFromUrl(url: string | null | undefined): string | undefined {
  if (!url) return undefined;
  try {
    return new URL(url, "http://local").searchParams.get("cursor") ?? undefined;
  } catch {
    return undefined;
  }
}
