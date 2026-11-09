import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { NotificationList } from "@/components/notifications/NotificationList";
import { PageHeader } from "@/components/PageHeader";
import { ButtonLink } from "@/components/ui/Button";
import { routes } from "@/lib/routes";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("notifications");
  return { title: t("title"), robots: { index: false } };
}

export default async function NotificationsPage() {
  const t = await getTranslations("notifications");
  return (
    <>
      <PageHeader
        title={t("title")}
        actions={
          <ButtonLink href={routes.account} variant="ghost" size="sm">
            {t("preferences")}
          </ButtonLink>
        }
      />
      <section className="kreo-container max-w-3xl py-8">
        <NotificationList />
      </section>
    </>
  );
}
