"use client";

import { ApiError } from "@kreo/api-client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useState, type ReactNode } from "react";

import { ToastProvider } from "@/components/ui/Toast";

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        refetchOnWindowFocus: false,
        retry: (failureCount, error) => {
          if (error instanceof ApiError && error.status < 500) return false;
          return failureCount < 2;
        },
      },
    },
  });
}

/** Fournisseurs côté client : cache react-query et notifications toast. */
export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(makeQueryClient);
  const t = useTranslations("common");
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider closeLabel={t("close")}>{children}</ToastProvider>
    </QueryClientProvider>
  );
}
