"use client";

import { useMutation } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { useId, useState, type FormEvent } from "react";

import { Button, ButtonLink } from "@/components/ui/Button";
import { useErrorMessage } from "@/hooks/useErrorMessage";
import { api, unwrap } from "@/lib/api/client";
import { errorFields } from "@/lib/api/errors";
import { routes } from "@/lib/routes";

import { FormError } from "./FormError";
import { PasswordField } from "./PasswordField";

/** Choix d'un nouveau mot de passe à partir du jeton reçu par e-mail. */
export function ResetPasswordForm() {
  const t = useTranslations("auth.reset");
  const tRegister = useTranslations("auth.register");
  const describeError = useErrorMessage();
  const id = useId();
  const token = useSearchParams().get("token");
  const [password, setPassword] = useState("");
  const mutation = useMutation({
    mutationFn: async () =>
      unwrap(
        await api.POST("/api/v1/auth/password-reset/confirm", {
          body: { token: token ?? "", password },
        }),
      ),
  });

  if (!token) {
    return (
      <div className="flex flex-col gap-4">
        <p role="alert" className="text-sm text-bordeaux">
          {t("invalidLink")}
        </p>
        <ButtonLink href={routes.forgotPassword} variant="secondary">
          {t("title")}
        </ButtonLink>
      </div>
    );
  }

  if (mutation.isSuccess) {
    return (
      <div className="flex flex-col gap-4" role="status">
        <p className="text-base text-brown">{t("done")}</p>
        <ButtonLink href={routes.login()}>{t("goLogin")}</ButtonLink>
      </div>
    );
  }

  const fieldError = mutation.isError ? errorFields(mutation.error).password : undefined;
  const submit = (event: FormEvent) => {
    event.preventDefault();
    mutation.mutate();
  };

  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-5">
      <FormError message={mutation.isError && !fieldError ? describeError(mutation.error) : null} />
      <PasswordField
        id={`${id}-password`}
        label={t("newPassword")}
        hint={tRegister("passwordHint")}
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        error={fieldError}
        autoComplete="new-password"
        minLength={10}
        required
      />
      <Button type="submit" size="lg" loading={mutation.isPending}>
        {t("submit")}
      </Button>
    </form>
  );
}
