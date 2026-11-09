/** Base publique de l'API, ex. http://localhost:8000/api/v1 (variable NEXT_PUBLIC_API_URL). */
export const API_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"
).replace(/\/$/, "");

/**
 * Les chemins générés dans `@kreo/api-client` incluent déjà `/api/v1` :
 * la base passée à openapi-fetch est donc l'origine seule.
 */
export const API_ORIGIN = API_URL.replace(/\/api\/v1$/, "");

export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000").replace(
  /\/$/,
  "",
);

/** Version des CGU acceptées à l'inscription. */
export const TERMS_VERSION = "2026-11";

/** Nom du cookie d'accès posé par l'API (contrôle de présence côté middleware). */
export const ACCESS_COOKIE = "kreo_access";
