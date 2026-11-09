"use client";

import { useMutation } from "@tanstack/react-query";
import { Download } from "lucide-react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";
import { useErrorMessage } from "@/hooks/useErrorMessage";
import { api, unwrap } from "@/lib/api/client";

/** Télécharge GET /me/export sous forme de fichier JSON (portabilité RGPD). */
export function ExportButton() {
  const t = useTranslations("account");
  const describeError = useErrorMessage();
  const { toast } = useToast();
  const mutation = useMutation({
    mutationFn: async () => unwrap(await api.GET("/api/v1/me/export")),
    onSuccess: (data) => {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `kreo-export-${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    },
    onError: (error) => toast(describeError(error), "error"),
  });
  return (
    <Button
      variant="secondary"
      icon={<Download aria-hidden="true" className="size-4" strokeWidth={1.5} />}
      loading={mutation.isPending}
      onClick={() => mutation.mutate()}
    >
      {t("export")}
    </Button>
  );
}
