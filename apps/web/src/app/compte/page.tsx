import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { getTranslations } from "next-intl/server";

import { DeleteAccount } from "@/components/account/DeleteAccount";
import { ExportButton } from "@/components/account/ExportButton";
import { NotificationPreferences } from "@/components/account/NotificationPreferences";
import { PageHeader } from "@/components/PageHeader";
import { Card } from "@/components/ui/Card";
import { getCurrentUser } from "@/lib/auth";
import { routes } from "@/lib/routes";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("account");
  return { title: t("title"), robots: { index: false } };
}

const LOCALE_LABELS: Record<string, string> = { fr: "Français", nl: "Nederlands", en: "English" };

export default async function AccountPage() {
  const user = await getCurrentUser();
  if (!user) redirect(routes.login(routes.account));
  const t = await getTranslations("account");

  return (
    <>
      <PageHeader title={t("title")} />
      <div className="kreo-container flex max-w-3xl flex-col gap-6 py-10">
        <Card as="section" aria-labelledby="identite">
          <h2 id="identite" className="text-base normal-case tracking-normal">
            {t("title")}
          </h2>
          <dl className="mt-4 grid gap-4 sm:grid-cols-2">
            <div>
              <dt className="text-xs tracking-caps text-taupe-dark uppercase">{t("email")}</dt>
              <dd className="mt-1 text-sm text-brown">{user.email}</dd>
            </div>
            <div>
              <dt className="text-xs tracking-caps text-taupe-dark uppercase">{t("locale")}</dt>
              <dd className="mt-1 text-sm text-brown">
                {LOCALE_LABELS[user.locale ?? "fr"] ?? user.locale}
                <span className="block text-xs text-taupe-dark">{t("localeNote")}</span>
              </dd>
            </div>
          </dl>
        </Card>

        <Card as="section" aria-labelledby="donnees">
          <h2 id="donnees" className="text-base normal-case tracking-normal">
            {t("data")}
          </h2>
          <p className="mt-2 text-sm text-taupe-dark">{t("exportHint")}</p>
          <div className="mt-4">
            <ExportButton />
          </div>
        </Card>

        <Card as="section" aria-labelledby="preferences">
          <h2 id="preferences" className="text-base normal-case tracking-normal">
            {t("preferences")}
          </h2>
          <div className="mt-4">
            <NotificationPreferences />
          </div>
        </Card>

        <Card as="section" aria-labelledby="danger" className="border-bordeaux/30">
          <h2 id="danger" className="text-base normal-case tracking-normal text-bordeaux">
            {t("danger")}
          </h2>
          <p className="mt-2 text-sm text-taupe-dark">{t("deleteBody")}</p>
          <div className="mt-4">
            <DeleteAccount />
          </div>
        </Card>
      </div>
    </>
  );
}
