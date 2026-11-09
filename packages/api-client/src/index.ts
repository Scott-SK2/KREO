import createClient, { type Middleware } from "openapi-fetch";

import type { paths } from "./schema";
import { ApiError, isProblem } from "./problem";

export * from "./problem";
export type { paths, components, operations } from "./schema";

export interface KreoClientOptions {
  /** Base de l'API, ex. http://localhost:8000/api/v1 */
  baseUrl: string;
  /** "web" (cookies HttpOnly) ou "mobile" (jetons dans le corps, en-tête Authorization). */
  client?: "web" | "mobile";
  /** Mobile : fournit le jeton d'accès courant. */
  getAccessToken?: () => Promise<string | null> | string | null;
  /** Appelé sur 401 pour tenter un rafraîchissement ; renvoie true si la requête peut être rejouée. */
  onUnauthorized?: () => Promise<boolean>;
  /** Permet d'injecter un fetch (Next.js côté serveur, tests). */
  fetch?: typeof globalThis.fetch;
  /** En-têtes supplémentaires (ex. cookies relayés côté serveur). */
  headers?: () => Promise<Record<string, string>> | Record<string, string>;
}

/**
 * Crée un client typé. Toutes les réponses d'erreur sont des `Problem` ;
 * utilise `unwrap()` pour obtenir soit les données, soit une `ApiError`.
 */
export function createKreoClient(options: KreoClientOptions) {
  const client = createClient<paths>({
    baseUrl: options.baseUrl,
    credentials: options.client === "mobile" ? "omit" : "include",
    fetch: options.fetch,
  });

  const auth: Middleware = {
    async onRequest({ request }) {
      request.headers.set("Accept", "application/json, application/problem+json");
      request.headers.set("X-Client", options.client ?? "web");
      if (options.headers) {
        for (const [k, v] of Object.entries(await options.headers())) request.headers.set(k, v);
      }
      if (options.getAccessToken) {
        const token = await options.getAccessToken();
        if (token) request.headers.set("Authorization", `Bearer ${token}`);
      }
      return request;
    },
  };
  client.use(auth);
  return client;
}

export type KreoClient = ReturnType<typeof createKreoClient>;

/** Transforme un résultat openapi-fetch `{ data, error, response }` en données ou lève une `ApiError`. */
export function unwrap<T>(result: { data?: T; error?: unknown; response: Response }): T {
  if (result.error !== undefined) {
    if (isProblem(result.error)) throw new ApiError(result.error);
    throw new ApiError({
      type: "https://kreo.be/problems/unknown",
      title: "Erreur",
      status: result.response.status,
      detail: typeof result.error === "string" ? result.error : undefined,
    });
  }
  return result.data as T;
}
