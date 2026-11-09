"use client";

import { useMutation } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useId, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { TextField } from "@/components/ui/TextField";
import { useErrorMessage } from "@/hooks/useErrorMessage";
import { api, unwrap } from "@/lib/api/client";

import { FormError } from "./FormError";

/** Demande de lien de réinitialisation ; réponse neutre, qu'un compte existe ou non. */
export function ForgotPasswordForm() {
  const t = useTranslations("auth.reset");
  const describeError = useErrorMessage();
  const id = useId();
  const [email, setEmail] = useState("");
  const mutation = useMutation({
    mutationFn: async () =>
      unwrap(await api.POST("/api/v1/auth/password-reset", { body: { email: email.trim() } })),
  });

  if (mutation.isSuccess) {
    return (
      <p role="status" className="text-base text-brown">
        {t("sent")}
      </p>
    );
  }

  const submit = (event: FormEvent) => {
    event.preventDefault();
    mutation.mutate();
  };

  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-5">
      <FormError message={mutation.isError ? describeError(mutation.error) : null} />
      <TextField
        id={`${id}-email`}
        type="email"
        label={t("email")}
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        autoComplete="email"
        required
      />
      <Button type="submit" size="lg" loading={mutation.isPending}>
        {t("submit")}
      </Button>
    </form>
  );
}
