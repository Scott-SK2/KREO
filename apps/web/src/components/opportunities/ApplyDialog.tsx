"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useId, useState, type FormEvent } from "react";

import { Button, ButtonLink } from "@/components/ui/Button";
import { Checkbox } from "@/components/ui/Checkbox";
import { Dialog } from "@/components/ui/Dialog";
import { Textarea } from "@/components/ui/Textarea";
import { useToast } from "@/components/ui/Toast";
import { useErrorMessage } from "@/hooks/useErrorMessage";
import { api, unwrap } from "@/lib/api/client";
import { routes } from "@/lib/routes";

export interface ApplyDialogProps {
  roleId: string;
  roleTitle: string;
  opportunityId: string;
  /** Identifiant de ma candidature si elle existe déjà. */
  myApplicationId: string | null;
  isAuthenticated: boolean;
  disabled?: boolean;
}

/**
 * Bouton « Candidater » et sa boîte de dialogue : message facultatif,
 * confirmation de disponibilité, envoi vers POST /roles/{id}/applications.
 */
export function ApplyDialog({
  roleId,
  roleTitle,
  opportunityId,
  myApplicationId,
  isAuthenticated,
  disabled = false,
}: ApplyDialogProps) {
  const t = useTranslations();
  const { toast } = useToast();
  const describeError = useErrorMessage();
  const router = useRouter();
  const queryClient = useQueryClient();
  const id = useId();
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [available, setAvailable] = useState(false);
  const [sentId, setSentId] = useState<string | null>(myApplicationId);

  const mutation = useMutation({
    mutationFn: async () =>
      unwrap(
        await api.POST("/api/v1/roles/{role_id}/applications", {
          params: { path: { role_id: roleId } },
          body: { message, availability_confirmed: available },
        }),
      ),
    onSuccess: (application) => {
      setSentId(application.id);
      setOpen(false);
      toast(t("application.sent"), "success");
      void queryClient.invalidateQueries({ queryKey: ["applications"] });
      router.refresh();
    },
    onError: (error) => toast(describeError(error), "error"),
  });

  if (sentId) {
    return (
      <ButtonLink href={routes.application(sentId)} variant="secondary" size="sm">
        {t("opportunity.applied")}
      </ButtonLink>
    );
  }

  if (!isAuthenticated) {
    return (
      <ButtonLink
        href={routes.login(routes.opportunity(opportunityId))}
        variant="secondary"
        size="sm"
      >
        {t("opportunity.loginToApply")}
      </ButtonLink>
    );
  }

  const submit = (event: FormEvent) => {
    event.preventDefault();
    mutation.mutate();
  };

  return (
    <>
      <Button size="sm" onClick={() => setOpen(true)} disabled={disabled}>
        {t("opportunity.apply")}
      </Button>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title={t("application.title", { role: roleTitle })}
        closeLabel={t("common.close")}
      >
        <form onSubmit={submit} className="flex flex-col gap-5">
          <Textarea
            id={`${id}-message`}
            label={t("application.message")}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            maxLength={1000}
            rows={4}
          />
          <Checkbox
            id={`${id}-availability`}
            label={t("application.availability")}
            checked={available}
            onChange={(e) => setAvailable(e.target.checked)}
          />
          <div className="flex flex-wrap justify-end gap-2">
            <Button variant="ghost" onClick={() => setOpen(false)}>
              {t("common.cancel")}
            </Button>
            <Button type="submit" loading={mutation.isPending}>
              {t("application.submit")}
            </Button>
          </div>
        </form>
      </Dialog>
    </>
  );
}
