"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useId, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { TextField } from "@/components/ui/TextField";
import { useToast } from "@/components/ui/Toast";
import { ME_QUERY_KEY } from "@/hooks/useMe";
import { useErrorMessage } from "@/hooks/useErrorMessage";
import { api, unwrap } from "@/lib/api/client";

/**
 * Vérification du numéro en deux temps sur le même endpoint :
 * `{ phone_number }` puis `{ code }`. En développement l'API renvoie `debug_code`.
 */
export function PhoneVerification() {
  const t = useTranslations("dashboard");
  const describeError = useErrorMessage();
  const { toast } = useToast();
  const router = useRouter();
  const queryClient = useQueryClient();
  const id = useId();
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [debugCode, setDebugCode] = useState<string | null>(null);
  const [stage, setStage] = useState<"number" | "code" | "done">("number");
  const [error, setError] = useState<string | null>(null);

  const start = useMutation({
    mutationFn: async () => {
      const data = unwrap(
        await api.POST("/api/v1/auth/phone/verify", { body: { phone_number: phone.trim() } }),
      );
      // Étape 1 : 202 avec un corps libre ({ debug_code } en développement).
      return (data ?? {}) as unknown as { debug_code?: string };
    },
    onSuccess: (body) => {
      setDebugCode(body.debug_code ?? null);
      setStage("code");
      setError(null);
    },
    onError: (err) => setError(describeError(err)),
  });

  const confirm = useMutation({
    mutationFn: async () =>
      unwrap(
        await api.POST("/api/v1/auth/phone/verify", {
          // L'API attend `code` à l'étape 2 ; le schéma OpenAPI ne décrit que l'étape 1.
          body: { code: code.trim() } as unknown as { phone_number: string },
        }),
      ),
    onSuccess: async () => {
      setStage("done");
      setError(null);
      toast(t("phone.done"), "success");
      await queryClient.invalidateQueries({ queryKey: ME_QUERY_KEY });
      router.refresh();
    },
    onError: (err) => setError(describeError(err)),
  });

  if (stage === "done") {
    return (
      <p role="status" className="text-sm font-medium text-success">
        {t("phone.done")}
      </p>
    );
  }

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (stage === "number") start.mutate();
    else confirm.mutate();
  };

  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-4">
      <p className="text-sm text-brown">{t("verifyPhone")}</p>
      {error ? (
        <p role="alert" className="text-sm font-medium text-bordeaux">
          {error}
        </p>
      ) : null}
      {stage === "number" ? (
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <TextField
            id={`${id}-phone`}
            type="tel"
            label={t("phone.number")}
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            autoComplete="tel"
            inputMode="tel"
            placeholder="+32470000000"
            wrapperClassName="flex-1"
            required
          />
          <Button type="submit" variant="secondary" loading={start.isPending}>
            {t("phone.send")}
          </Button>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          <p role="status" className="text-sm text-taupe-dark">
            {t("phone.sent")}
          </p>
          {debugCode ? (
            <p className="rounded-md border border-dashed border-gold bg-gold/10 px-3 py-2 text-sm text-brown">
              {t("phone.debugCode", { code: debugCode })}
            </p>
          ) : null}
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <TextField
              id={`${id}-code`}
              label={t("phone.code")}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              inputMode="numeric"
              autoComplete="one-time-code"
              wrapperClassName="flex-1"
              required
            />
            <Button type="submit" loading={confirm.isPending}>
              {t("phone.verify")}
            </Button>
          </div>
        </div>
      )}
    </form>
  );
}
