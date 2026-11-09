import { ApiError, createKreoClient, unwrap } from "@kreo/api-client";
import { cookies } from "next/headers";

import { API_ORIGIN } from "./config";

/**
 * Client API côté serveur : relaie les cookies de la requête entrante
 * (`kreo_access`) vers l'API Django. À utiliser dans les Server Components,
 * les route handlers et les Server Actions.
 */
export async function serverApi() {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();
  return createKreoClient({
    baseUrl: API_ORIGIN,
    client: "web",
    fetch: (input, init) => fetch(input, { ...init, cache: "no-store" }),
    headers: (): Record<string, string> => (cookieHeader ? { cookie: cookieHeader } : {}),
  });
}

/**
 * Client API public (sans cookie) pour les pages anonymes, avec revalidation
 * incrémentale : les listes publiques tolèrent 60 s de latence.
 */
export function publicApi(revalidate = 60) {
  return createKreoClient({
    baseUrl: API_ORIGIN,
    client: "web",
    fetch: (input, init) => fetch(input, { ...init, next: { revalidate } }),
  });
}

/** Renvoie `null` au lieu de lever une erreur quand la ressource est 404 ou 401/403. */
export async function orNull<T>(promise: Promise<T>): Promise<T | null> {
  try {
    return await promise;
  } catch (error) {
    if (error instanceof ApiError && [401, 403, 404].includes(error.status)) return null;
    throw error;
  }
}

export { unwrap };
