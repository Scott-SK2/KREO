import { useTranslations } from "next-intl";

import { ButtonLink } from "@/components/ui/Button";
import { routes } from "@/lib/routes";

const MISSING_KEYS = [
  "display_name",
  "disciplines",
  "city",
  "bio",
  "avatar",
  "gallery",
  "links",
  "level",
] as const;
type MissingKey = (typeof MISSING_KEYS)[number];
const isMissingKey = (k: string): k is MissingKey =>
  (MISSING_KEYS as readonly string[]).includes(k);

/** Jauge de complétion du profil (score + éléments manquants, en mots simples). */
export function CompletionMeter({ score, missing }: { score: number; missing: string[] }) {
  const t = useTranslations("dashboard");
  const known = missing.filter(isMissingKey);
  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm font-medium text-brown">{t("completion", { percent: score })}</p>
      <div
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={score}
        aria-label={t("completion", { percent: score })}
        className="h-2 overflow-hidden rounded-full bg-ivory"
      >
        <div className="h-full rounded-full bg-gold" style={{ width: `${score}%` }} />
      </div>
      {known.length ? (
        <p className="text-sm text-taupe-dark">
          {t("missingIntro")} {known.map((k) => t(`missing.${k}`)).join(", ")}.
        </p>
      ) : (
        <p className="text-sm text-success">{t("completionDone")}</p>
      )}
      {score < 100 ? (
        <ButtonLink href={routes.onboarding} variant="secondary" size="sm" className="self-start">
          {t("completeProfile")}
        </ButtonLink>
      ) : null}
    </div>
  );
}
