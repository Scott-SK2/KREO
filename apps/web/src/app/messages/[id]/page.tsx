import { ArrowLeft } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";

import { ConversationList } from "@/components/messages/ConversationList";
import { ConversationThread } from "@/components/messages/ConversationThread";
import { orNull, serverApi, unwrap } from "@/lib/api/server";
import { routes } from "@/lib/routes";

type Params = Promise<{ id: string }>;

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("messages");
  return { title: t("title"), robots: { index: false } };
}

export default async function ConversationPage({ params }: { params: Params }) {
  const { id } = await params;
  const api = await serverApi();
  const [t, conversations] = await Promise.all([
    getTranslations("messages"),
    orNull(api.GET("/api/v1/conversations").then(unwrap)),
  ]);
  const conversation = conversations?.find((c) => c.id === id);
  if (!conversation) notFound();

  return (
    <div className="kreo-container py-8">
      <Link
        href={routes.messages}
        className="inline-flex min-h-touch items-center gap-1 text-sm text-taupe-dark underline-offset-4 hover:underline lg:hidden"
      >
        <ArrowLeft aria-hidden="true" className="size-4" strokeWidth={1.5} />
        {t("back")}
      </Link>
      <div className="grid gap-6 lg:grid-cols-[20rem_1fr]">
        <aside className="hidden lg:block">
          <h1 className="mb-4 text-2xl">{t("title")}</h1>
          <ConversationList activeId={id} />
        </aside>
        <section aria-label={conversation.project_title}>
          <ConversationThread conversation={conversation} />
        </section>
      </div>
    </div>
  );
}
