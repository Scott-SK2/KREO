"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { MessageSquare } from "lucide-react";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button, ButtonLink } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { useToast } from "@/components/ui/Toast";
import { useErrorMessage } from "@/hooks/useErrorMessage";
import { api, unwrap } from "@/lib/api/client";
import { routes } from "@/lib/routes";

export interface ApplicationActionsProps {
  applicationId: string;
  allowedTransitions: string[];
  conversationId: string | null;
}

const ACTIONS: {
  status: string;
  labelKey: "withdraw" | "acceptOffer" | "declineOffer";
  variant: "ghost" | "primary" | "secondary";
  confirm: boolean;
}[] = [
  { status: "accepted", labelKey: "acceptOffer", variant: "primary", confirm: false },
  { status: "declined", labelKey: "declineOffer", variant: "secondary", confirm: true },
  { status: "withdrawn", labelKey: "withdraw", variant: "ghost", confirm: true },
];

/** Actions du candidat selon `allowed_transitions`, plus l'accès à la conversation. */
export function ApplicationActions({
  applicationId,
  allowedTransitions,
  conversationId,
}: ApplicationActionsProps) {
  const t = useTranslations();
  const describeError = useErrorMessage();
  const { toast } = useToast();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [pendingConfirm, setPendingConfirm] = useState<string | null>(null);

  const transition = useMutation({
    mutationFn: async (status: string) =>
      unwrap(
        await api.POST("/api/v1/applications/{application_id}/transition", {
          params: { path: { application_id: applicationId } },
          body: { status, note: "" },
        }),
      ),
    onSuccess: async () => {
      setPendingConfirm(null);
      toast(t("application.transitionDone"), "success");
      await queryClient.invalidateQueries({ queryKey: ["applications"] });
      router.refresh();
    },
    onError: (error) => toast(describeError(error), "error"),
  });

  const openConversation = useMutation({
    mutationFn: async () =>
      unwrap(await api.POST("/api/v1/conversations", { body: { application_id: applicationId } })),
    onSuccess: (conversation) => router.push(routes.conversation(conversation.id)),
    onError: (error) => toast(describeError(error), "error"),
  });

  const available = ACTIONS.filter((a) => allowedTransitions.includes(a.status));
  const confirming = ACTIONS.find((a) => a.status === pendingConfirm);

  return (
    <div className="flex flex-wrap items-center gap-2">
      {conversationId ? (
        <ButtonLink
          href={routes.conversation(conversationId)}
          variant="secondary"
          icon={<MessageSquare aria-hidden="true" className="size-4" strokeWidth={1.5} />}
        >
          {t("application.openConversation")}
        </ButtonLink>
      ) : (
        <Button
          variant="secondary"
          icon={<MessageSquare aria-hidden="true" className="size-4" strokeWidth={1.5} />}
          loading={openConversation.isPending}
          onClick={() => openConversation.mutate()}
        >
          {t("application.startConversation")}
        </Button>
      )}
      {available.map((action) => (
        <Button
          key={action.status}
          variant={action.variant}
          loading={transition.isPending && transition.variables === action.status}
          onClick={() =>
            action.confirm ? setPendingConfirm(action.status) : transition.mutate(action.status)
          }
        >
          {t(`application.${action.labelKey}`)}
        </Button>
      ))}
      <Dialog
        open={pendingConfirm !== null}
        onClose={() => setPendingConfirm(null)}
        title={confirming ? t(`application.${confirming.labelKey}`) : ""}
        closeLabel={t("common.close")}
      >
        <div className="flex flex-wrap justify-end gap-2">
          <Button variant="ghost" onClick={() => setPendingConfirm(null)}>
            {t("common.cancel")}
          </Button>
          <Button
            variant={confirming?.status === "withdrawn" ? "danger" : "primary"}
            loading={transition.isPending}
            onClick={() => pendingConfirm && transition.mutate(pendingConfirm)}
          >
            {t("common.confirm")}
          </Button>
        </div>
      </Dialog>
    </div>
  );
}
