import { ShieldCheck } from "lucide-react";
import { useTranslations } from "next-intl";

/** Bloc de conseils de sécurité : liste fournie par l'API ou repli sur les clés i18n. */
export function SafetyTips({ tips, className }: { tips?: string[] | null; className?: string }) {
  const t = useTranslations();
  const list = tips?.length
    ? tips
    : [t("messages.safety.meet"), t("messages.safety.pay"), t("messages.safety.report")];
  return (
    <aside
      aria-label={t("opportunity.safetyTitle")}
      className={`rounded-xl border border-gold/40 bg-gold/10 p-5 ${className ?? ""}`}
    >
      <h2 className="flex items-center gap-2 text-base normal-case tracking-normal">
        <ShieldCheck aria-hidden="true" className="size-5 text-taupe-dark" strokeWidth={1.5} />
        {t("opportunity.safetyTitle")}
      </h2>
      <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-brown">
        {list.map((tip) => (
          <li key={tip}>{tip}</li>
        ))}
      </ul>
    </aside>
  );
}
