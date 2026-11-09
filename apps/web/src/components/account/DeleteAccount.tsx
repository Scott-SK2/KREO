"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { useToast } from "@/components/ui/Toast";
import { useErrorMessage } from "@/hooks/useErrorMessage";
import { api } from "@/lib/api/client";

/** Suppression du compte : confirmation explicite puis DELETE /me et retour à l'accueil. */
export function DeleteAccount() {
  const t = useTranslations("account");
  const tCommon = useTranslations("common");
  const describeError = useErrorMessage();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);

  const mutation = useMutation({
    mutationFn: async () => {
      const { error, response } = await api.DELETE("/api/v1/me");
      if (error !== undefined || !response.ok) throw error ?? new Error(String(response.status));
    },
    onSuccess: () => {
      queryClient.clear();
      toast(t("deleted"), "success");
      window.setTimeout(() => window.location.assign("/"), 800);
    },
    onError: (error) => toast(describeError(error), "error"),
  });

  return (
    <>
      <Button
        variant="danger"
        icon={<Trash2 aria-hidden="true" className="size-4" strokeWidth={1.5} />}
        onClick={() => setOpen(true)}
      >
        {t("delete")}
      </Button>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title={t("deleteTitle")}
        description={t("deleteBody")}
        closeLabel={tCommon("close")}
      >
        <div className="flex flex-wrap justify-end gap-2">
          <Button variant="ghost" onClick={() => setOpen(false)}>
            {tCommon("cancel")}
          </Button>
          <Button variant="danger" loading={mutation.isPending} onClick={() => mutation.mutate()}>
            {t("deleteConfirm")}
          </Button>
        </div>
      </Dialog>
    </>
  );
}
