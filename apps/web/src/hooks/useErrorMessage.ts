"use client";

import { useTranslations } from "next-intl";
import { useCallback } from "react";

import { errorMessage, type ErrorTranslator } from "@/lib/api/errors";

/** Renvoie `describe(error)` : message français d'une erreur API ou réseau. */
export function useErrorMessage() {
  const t = useTranslations("errors");
  return useCallback((error: unknown) => errorMessage(error, t as unknown as ErrorTranslator), [t]);
}
