"use client";

import type { components } from "@kreo/api-client";
import { Check, Copy } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";
import { formatDate } from "@/lib/format";

type BetaInvitation = components["schemas"]["BetaInvitation"];

/** Codes d'invitation du membre avec bouton « Copier » et compteur restant. */
export function InvitationsList({
  invitations,
  left,
}: {
  invitations: BetaInvitation[];
  left: number;
}) {
  const t = useTranslations("dashboard");
  const { toast } = useToast();
  const [copied, setCopied] = useState<string | null>(null);

  const copy = async (code: string) => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(code);
      toast(t("copied"), "success");
      window.setTimeout(() => setCopied(null), 2000);
    } catch {
      // Presse-papiers indisponible : le code reste sélectionnable à la main.
    }
  };

  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm text-taupe-dark">{t("invitationsLeft", { count: left })}</p>
      {invitations.length ? (
        <ul className="flex flex-col gap-2">
          {invitations.map((inv) => (
            <li
              key={inv.code ?? inv.created_at}
              className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-taupe/15 bg-ivory/40 px-3 py-2"
            >
              <div className="min-w-0">
                <code className="font-mono text-sm font-medium tracking-wider text-brown select-all">
                  {inv.code ?? "—"}
                </code>
                <p className="text-xs text-taupe-dark">
                  {inv.used
                    ? t("invitationUsed")
                    : inv.expires_at
                      ? t("invitationExpires", { date: formatDate(inv.expires_at) })
                      : ""}
                </p>
              </div>
              {inv.used ? (
                <Badge>{t("invitationUsed")}</Badge>
              ) : inv.code ? (
                <Button
                  variant="ghost"
                  size="sm"
                  icon={
                    copied === inv.code ? (
                      <Check aria-hidden="true" className="size-4 text-success" strokeWidth={1.5} />
                    ) : (
                      <Copy aria-hidden="true" className="size-4" strokeWidth={1.5} />
                    )
                  }
                  onClick={() => void copy(inv.code ?? "")}
                >
                  {t("copyCode")}
                </Button>
              ) : null}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-taupe-dark">{t("noInvitations")}</p>
      )}
    </div>
  );
}
