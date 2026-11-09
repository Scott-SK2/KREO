import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { ApplicationsList } from "@/components/applications/ApplicationsList";
import { PageHeader } from "@/components/PageHeader";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("nav");
  return { title: t("myApplications"), robots: { index: false } };
}

export default async function ApplicationsPage() {
  const t = await getTranslations("nav");
  return (
    <>
      <PageHeader title={t("myApplications")} />
      <section className="kreo-container py-8">
        <ApplicationsList />
      </section>
    </>
  );
}
