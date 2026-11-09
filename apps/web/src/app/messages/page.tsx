import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { ConversationList } from "@/components/messages/ConversationList";
import { PageHeader } from "@/components/PageHeader";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("messages");
  return { title: t("title"), robots: { index: false } };
}

export default async function MessagesPage() {
  const t = await getTranslations("messages");
  return (
    <>
      <PageHeader title={t("title")} />
      <section className="kreo-container max-w-3xl py-8">
        <ConversationList />
      </section>
    </>
  );
}
