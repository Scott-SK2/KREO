import { getTranslations } from "next-intl/server";

import { PageHeader } from "@/components/PageHeader";
import { TERMS_VERSION } from "@/lib/api/config";

type LegalKind = "terms" | "privacy" | "charter";
const BODY_KEY = { terms: "termsBody", privacy: "privacyBody", charter: "charterBody" } as const;

/** Page légale provisoire : titre, mention « à relire par un juriste », texte court. */
export async function LegalPage({ kind }: { kind: LegalKind }) {
  const t = await getTranslations("legal");
  return (
    <>
      <PageHeader title={t(`${kind}.title`)} eyebrow={t("version", { version: TERMS_VERSION })} />
      <article className="kreo-container max-w-3xl py-10">
        <p className="rounded-md border border-dashed border-warning/60 bg-warning/10 px-4 py-3 text-sm text-warning">
          {t("placeholder")}
        </p>
        <div className="kreo-prose mt-6">
          <p>{t(BODY_KEY[kind])}</p>
        </div>
      </article>
    </>
  );
}
