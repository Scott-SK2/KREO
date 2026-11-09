"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useId, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { TextField } from "@/components/ui/TextField";
import { useToast } from "@/components/ui/Toast";
import { ME_QUERY_KEY } from "@/hooks/useMe";
import { useErrorMessage } from "@/hooks/useErrorMessage";
import { api, unwrap } from "@/lib/api/client";
import { API_ORIGIN } from "@/lib/api/config";
import { errorSlug } from "@/lib/api/errors";
import { routes } from "@/lib/routes";

import { FormError } from "./FormError";
import { PasswordField } from "./PasswordField";

/** Destination après connexion : chemin interne uniquement (anti open-redirect). */
export function safeNext(value: string | null, fallback: string): string {
  if (!value || !value.startsWith("/") || value.startsWith("//")) return fallback;
  return value;
}

/** Connexion par e-mail et mot de passe ; respecte `?next=`. */
export function LoginForm() {
  const t = useTranslations("auth.login");
  const describeError = useErrorMessage();
  const { toast } = useToast();
  const router = useRouter();
  const queryClient = useQueryClient();
  const searchParams = useSearchParams();
  const id = useId();
  const next = safeNext(searchParams.get("next"), routes.dashboard);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [unverified, setUnverified] = useState(false);
  const [resuming, setResuming] = useState(Boolean(searchParams.get("next")));

  // Session expirée mais cookie de rafraîchissement encore valide : on reprend sans ressaisie.
  useEffect(() => {
    if (!resuming) return;
    let cancelled = false;
    fetch(`${API_ORIGIN}/api/v1/auth/refresh`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    })
      .then((res) => {
        if (!cancelled && res.ok) {
          router.replace(next);
          router.refresh();
        } else if (!cancelled) setResuming(false);
      })
      .catch(() => {
        if (!cancelled) setResuming(false);
      });
    return () => {
      cancelled = true;
    };
  }, [resuming, next, router]);

  const login = useMutation({
    mutationFn: async () =>
      unwrap(await api.POST("/api/v1/auth/login", { body: { email: email.trim(), password } })),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ME_QUERY_KEY });
      router.replace(next);
      router.refresh();
    },
    onError: (err) => {
      setUnverified(errorSlug(err) === "email-not-verified");
      setError(describeError(err));
    },
  });

  const resend = useMutation({
    mutationFn: async () =>
      unwrap(await api.POST("/api/v1/auth/resend-verification", { body: { email: email.trim() } })),
    onSuccess: () => toast(t("emailNotVerified"), "success"),
    onError: (err) => toast(describeError(err), "error"),
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    login.mutate();
  };

  if (resuming) {
    return (
      <p role="status" className="text-sm text-taupe-dark">
        {t("resumed")}
      </p>
    );
  }

  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-5">
      <FormError message={error} />
      {unverified ? (
        <Button
          variant="secondary"
          size="sm"
          loading={resend.isPending}
          onClick={() => resend.mutate()}
        >
          {t("emailNotVerified")}
        </Button>
      ) : null}
      <TextField
        id={`${id}-email`}
        type="email"
        label={t("email")}
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        autoComplete="email"
        inputMode="email"
        required
      />
      <PasswordField
        id={`${id}-password`}
        label={t("password")}
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        autoComplete="current-password"
        required
      />
      <div className="flex items-center justify-between gap-3">
        <Link
          href={routes.forgotPassword}
          className="inline-flex min-h-touch items-center text-sm text-taupe-dark underline-offset-4 hover:underline"
        >
          {t("forgot")}
        </Link>
        <Button type="submit" size="lg" loading={login.isPending}>
          {t("submit")}
        </Button>
      </div>
    </form>
  );
}
