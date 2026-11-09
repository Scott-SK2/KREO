import { ApiError, type components } from "@kreo/api-client";
import { cookies } from "next/headers";

import { ACCESS_COOKIE } from "./api/config";
import { serverApi, unwrap } from "./api/server";

export type Me = components["schemas"]["Me"];

/**
 * Utilisateur courant côté serveur, ou `null` si anonyme (cookie absent ou 401).
 * Ne lève jamais pour un simple problème d'authentification.
 */
export async function getCurrentUser(): Promise<Me | null> {
  const cookieStore = await cookies();
  if (!cookieStore.get(ACCESS_COOKIE)) return null;
  try {
    const api = await serverApi();
    return unwrap(await api.GET("/api/v1/me"));
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) return null;
    if (error instanceof TypeError) return null;
    throw error;
  }
}
