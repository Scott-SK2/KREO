"use client";

import { useMutation } from "@tanstack/react-query";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { useId, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { Checkbox } from "@/components/ui/Checkbox";
import { TextField } from "@/components/ui/TextField";
import { useToast } from "@/components/ui/Toast";
import { useErrorMessage } from "@/hooks/useErrorMessage";
import { api, unwrap } from "@/lib/api/client";
import { TERMS_VERSION } from "@/lib/api/config";
import { errorFields, errorSlug } from "@/lib/api/errors";
import { routes } from "@/lib/routes";

import { FormError } from "./FormError";
import { PasswordField } from "./PasswordField";

/** Slugs de problème rattachés à un champ précis du formulaire. */
const SLUG_TO_FIELD: Record<string, string> = {
  "invitation-invalid": "invitation_code",
  "minimum-age": "birth_date",
  "email-taken": "email",
};

/** Inscription sur invitation : code, e-mail, mot de passe, date de naissance, CGU. */
export function RegisterForm() {
  const t = useTranslations("auth.register");
  const tCommon = useTranslations("common");
  const describeError = useErrorMessage();
  const { toast } = useToast();
  const id = useId();
  const searchParams = useSearchParams();
  const [form, setForm] = useState({
    invitation_code: searchParams.get("code") ?? "",
    email: "",
    password: "",
    birth_date: "",
    terms: false,
  });
  const [fieldErrs, setFieldErrs] = useState<Record<string, string>>({});
  const [globalErr, setGlobalErr] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const register = useMutation({
    mutationFn: async () =>
      unwrap(
        await api.POST("/api/v1/auth/register", {
          body: {
            email: form.email.trim(),
            password: form.password,
            invitation_code: form.invitation_code.trim(),
            birth_date: form.birth_date,
            terms_version: TERMS_VERSION,
            locale: "fr",
          },
        }),
      ),
    onSuccess: () => setDone(true),
    onError: (error) => {
      const fields = errorFields(error);
      const slug = errorSlug(error);
      const message = describeError(error);
      const field = SLUG_TO_FIELD[slug];
      if (field && !fields[field]) fields[field] = message;
      setFieldErrs(fields);
      setGlobalErr(field || Object.keys(fields).length ? (fields._ ?? null) : message);
    },
  });

  const resend = useMutation({
    mutationFn: async () =>
      unwrap(
        await api.POST("/api/v1/auth/resend-verification", { body: { email: form.email.trim() } }),
      ),
    onSuccess: () => toast(t("resent"), "success"),
    onError: (error) => toast(describeError(error), "error"),
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setFieldErrs({});
    setGlobalErr(null);
    if (!form.terms) {
      setFieldErrs({ terms: tCommon("required") });
      return;
    }
    register.mutate();
  };

  if (done) {
    return (
      <div className="flex flex-col gap-4" role="status">
        <p className="text-base text-brown">{t("success")}</p>
        <Button variant="secondary" loading={resend.isPending} onClick={() => resend.mutate()}>
          {t("resend")}
        </Button>
      </div>
    );
  }

  const update = (key: keyof typeof form, value: string | boolean) =>
    setForm((f) => ({ ...f, [key]: value }));

  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-5">
      <FormError message={globalErr} />
      <TextField
        id={`${id}-code`}
        label={t("invitationCode")}
        value={form.invitation_code}
        onChange={(e) => update("invitation_code", e.target.value)}
        error={fieldErrs.invitation_code}
        autoComplete="off"
        autoCapitalize="characters"
        required
      />
      <TextField
        id={`${id}-email`}
        type="email"
        label={t("email")}
        value={form.email}
        onChange={(e) => update("email", e.target.value)}
        error={fieldErrs.email}
        autoComplete="email"
        inputMode="email"
        required
      />
      <PasswordField
        id={`${id}-password`}
        label={t("password")}
        hint={t("passwordHint")}
        value={form.password}
        onChange={(e) => update("password", e.target.value)}
        error={fieldErrs.password}
        autoComplete="new-password"
        minLength={10}
        required
      />
      <TextField
        id={`${id}-birth`}
        type="date"
        label={t("birthDate")}
        hint={t("birthDateHint")}
        value={form.birth_date}
        onChange={(e) => update("birth_date", e.target.value)}
        error={fieldErrs.birth_date}
        autoComplete="bday"
        required
      />
      <Checkbox
        id={`${id}-terms`}
        checked={form.terms}
        onChange={(e) => update("terms", e.target.checked)}
        error={fieldErrs.terms}
        label={
          <>
            {t("terms")}{" "}
            <Link href={routes.terms} className="underline underline-offset-4">
              ({tCommon("more")})
            </Link>
          </>
        }
      />
      <Button type="submit" size="lg" loading={register.isPending}>
        {t("submit")}
      </Button>
    </form>
  );
}
