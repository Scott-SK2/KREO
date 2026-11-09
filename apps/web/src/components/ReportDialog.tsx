"use client";

import type { components } from "@kreo/api-client";
import { useMutation } from "@tanstack/react-query";
import { Flag } from "lucide-react";
import { useTranslations } from "next-intl";
import { useId, useState, type FormEvent } from "react";

import { Button, ButtonLink } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { Select } from "@/components/ui/Select";
import { Textarea } from "@/components/ui/Textarea";
import { useToast } from "@/components/ui/Toast";
import { useErrorMessage } from "@/hooks/useErrorMessage";
import { api, unwrap } from "@/lib/api/client";
import { routes } from "@/lib/routes";

type Reason = components["schemas"]["ReasonEnum"];
type TargetType = components["schemas"]["ReportTargetTypeEnum"];

const REASONS: Reason[] = [
  "harassment",
  "threats",
  "minor_safety",
  "sexual_content",
  "scam_money",
  "discrimination",
  "spam",
  "fake_casting",
  "private_audition",
  "inappropriate",
  "other",
];

export interface ReportDialogProps {
  targetType: TargetType;
  targetId: string;
  isAuthenticated: boolean;
  /** Page vers laquelle revenir après connexion. */
  returnTo: string;
  label: string;
}

/** Lien discret « Signaler » ouvrant un court formulaire vers POST /reports. */
export function ReportDialog({
  targetType,
  targetId,
  isAuthenticated,
  returnTo,
  label,
}: ReportDialogProps) {
  const t = useTranslations();
  const { toast } = useToast();
  const describeError = useErrorMessage();
  const id = useId();
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState<Reason>("inappropriate");
  const [details, setDetails] = useState("");

  const mutation = useMutation({
    mutationFn: async () =>
      unwrap(
        await api.POST("/api/v1/reports", {
          body: { target_type: targetType, target_id: targetId, reason, details },
        }),
      ),
    onSuccess: () => {
      setOpen(false);
      setDetails("");
      toast(t("report.sent"), "success");
    },
    onError: (error) => toast(describeError(error), "error"),
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    mutation.mutate();
  };

  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        icon={<Flag aria-hidden="true" className="size-4" strokeWidth={1.5} />}
        onClick={() => setOpen(true)}
        className="text-bordeaux hover:bg-bordeaux/10"
      >
        {label}
      </Button>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title={t("report.title")}
        description={t("report.intro")}
        closeLabel={t("common.close")}
      >
        {isAuthenticated ? (
          <form onSubmit={submit} className="flex flex-col gap-5">
            <Select
              id={`${id}-reason`}
              label={t("report.reason")}
              value={reason}
              onChange={(e) => setReason(e.target.value as Reason)}
              options={REASONS.map((r) => ({ value: r, label: t(`report.reasons.${r}`) }))}
            />
            <Textarea
              id={`${id}-details`}
              label={t("report.details")}
              value={details}
              onChange={(e) => setDetails(e.target.value)}
              maxLength={2000}
              rows={4}
            />
            <div className="flex flex-wrap justify-end gap-2">
              <Button variant="ghost" onClick={() => setOpen(false)}>
                {t("common.cancel")}
              </Button>
              <Button type="submit" variant="danger" loading={mutation.isPending}>
                {t("report.submit")}
              </Button>
            </div>
          </form>
        ) : (
          <div className="flex flex-col gap-4">
            <p className="text-sm text-taupe-dark">{t("report.loginRequired")}</p>
            <ButtonLink href={routes.login(returnTo)} variant="secondary">
              {t("nav.login")}
            </ButtonLink>
          </div>
        )}
      </Dialog>
    </>
  );
}
