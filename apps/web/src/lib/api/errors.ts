import { ApiError, fieldErrors, type Problem } from "@kreo/api-client";

/** Fonction de traduction minimale (compatible `useTranslations("errors")`). */
export type ErrorTranslator = {
  (key: string): string;
  has?: (key: string) => boolean;
};

const FALLBACK_KEY = "unknown";

/** Slug d'un problème ou "unknown" si l'erreur n'est pas une `ApiError`. */
export function errorSlug(error: unknown): string {
  if (error instanceof ApiError) return error.slug;
  if (error instanceof TypeError) return "network";
  return FALLBACK_KEY;
}

/**
 * Traduit une erreur (ApiError, TypeError réseau, autre) en message lisible.
 * Cherche `errors.<slug>` puis retombe sur `errors.unknown`.
 */
export function errorMessage(error: unknown, t: ErrorTranslator): string {
  const slug = errorSlug(error);
  if (t.has ? t.has(slug) : true) {
    const translated = t(slug);
    // next-intl renvoie la clé entre crochets quand elle manque.
    if (translated && !translated.startsWith("errors.") && !translated.includes(slug + "]")) {
      return translated;
    }
  }
  return t(FALLBACK_KEY);
}

/** Erreurs de champ d'un problème de validation ({ email: "…" }). */
export function errorFields(error: unknown): Record<string, string> {
  if (error instanceof ApiError) return fieldErrors(error.problem);
  return {};
}

/** Première erreur globale (champ null) renvoyée par l'API, si présente. */
export function globalFieldError(error: unknown): string | undefined {
  if (!(error instanceof ApiError)) return undefined;
  return errorFields(error)._;
}

export type { Problem };
export { ApiError };
