"use client";

import { ApiError, type components } from "@kreo/api-client";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { api, unwrap } from "@/lib/api/client";

export type Me = components["schemas"]["Me"];

export const ME_QUERY_KEY = ["me"] as const;

/** Utilisateur courant côté client (`null` si anonyme) ; 401 n'est pas une erreur. */
export function useMe(initialData?: Me | null) {
  return useQuery({
    queryKey: ME_QUERY_KEY,
    queryFn: async (): Promise<Me | null> => {
      try {
        return unwrap(await api.GET("/api/v1/me"));
      } catch (error) {
        if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
          return null;
        }
        throw error;
      }
    },
    initialData: initialData === undefined ? undefined : initialData,
    staleTime: 60_000,
  });
}

/** Déconnexion : l'API efface les cookies ; on vide le cache local. */
export function useLogout() {
  const queryClient = useQueryClient();
  return async () => {
    try {
      await api.POST("/api/v1/auth/logout");
    } finally {
      queryClient.clear();
      window.location.assign("/");
    }
  };
}
