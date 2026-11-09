"use client";

import { useMutation } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef } from "react";

import { Button, ButtonLink } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { useErrorMessage } from "@/hooks/useErrorMessage";
import { api, unwrap } from "@/lib/api/client";
import { routes } from "@/lib/routes";

/** Lit `?token=`, appelle POST /auth/verify-email puis redirige vers l'onboarding. */
export function VerifyEmail() {
  const t = useTranslations("auth.verifyEmail");
  const describeError = useErrorMessage();
  const router = useRouter();
  const token = useSearchParams().get("token");
  const started = useRef(false);

  const verify = useMutation({
    mutationFn: async (value: string) =>
      unwrap(await api.POST("/api/v1/auth/verify-email", { body: { token: value } })),
    onSuccess: () => {
      window.setTimeout(() => router.replace(routes.onboarding), 1200);
    },
  });

  useEffect(() => {
    if (token && !started.current) {
      started.current = true;
      verify.mutate(token);
    }
  }, [token, verify]);

  if (!token) {
    return (
      <div className="flex flex-col gap-4">
        <p role="alert" className="text-sm text-bordeaux">
          {t("missingToken")}
        </p>
        <ButtonLink href={routes.login()} variant="secondary">
          {t("resend")}
        </ButtonLink>
      </div>
    );
  }

  if (verify.isSuccess) {
    return (
      <div className="flex flex-col gap-4" role="status">
        <p className="text-base text-brown">{t("success")}</p>
        <ButtonLink href={routes.onboarding}>{t("goOnboarding")}</ButtonLink>
      </div>
    );
  }

  if (verify.isError) {
    return (
      <div className="flex flex-col gap-4">
        <p role="alert" className="text-sm text-bordeaux">
          {describeError(verify.error)}
        </p>
        <Button variant="secondary" onClick={() => verify.mutate(token)}>
          {t("resend")}
        </Button>
      </div>
    );
  }

  return (
    <p role="status" className="inline-flex items-center gap-2 text-sm text-taupe-dark">
      <Spinner className="size-4" />
      {t("verifying")}
    </p>
  );
}
