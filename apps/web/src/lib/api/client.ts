"use client";

import { createKreoClient, unwrap } from "@kreo/api-client";

import { API_ORIGIN } from "./config";

let refreshing: Promise<boolean> | null = null;

/** Tente une rotation du jeton via le cookie `kreo_refresh` (une seule à la fois). */
async function refreshSession(): Promise<boolean> {
  refreshing ??= fetch(`${API_ORIGIN}/api/v1/auth/refresh`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  })
    .then((res) => res.ok)
    .catch(() => false)
    .finally(() => {
      refreshing = null;
    });
  return refreshing;
}

/**
 * `fetch` navigateur : cookies inclus, et sur 401 une tentative de rafraîchissement
 * suivie d'un rejeu unique de la requête d'origine.
 */
async function browserFetch(input: Request | string | URL, init?: RequestInit): Promise<Response> {
  const request = input instanceof Request ? input : new Request(input, init);
  const isAuthRoute = request.url.includes("/api/v1/auth/");
  const first = await fetch(request.clone(), { credentials: "include" });
  if (first.status !== 401 || isAuthRoute) return first;
  const ok = await refreshSession();
  if (!ok) return first;
  return fetch(request, { credentials: "include" });
}

/** Client API côté navigateur (composants client, react-query). */
export const api = createKreoClient({
  baseUrl: API_ORIGIN,
  client: "web",
  fetch: browserFetch,
});

export { unwrap };
