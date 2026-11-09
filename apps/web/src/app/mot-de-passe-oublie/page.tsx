import type { Metadata } from "next";
import Link from "next/link";
import { getTranslations } from "next-intl/server";

import { AuthCard } from "@/components/auth/AuthCard";
import { ForgotPasswordForm } from "@/components/auth/ForgotPasswordForm";
import { routes } from "@/lib/routes";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("auth.reset");
  return { title: t("title"), robots: { index: false } };
}

export default async function ForgotPasswordPage() {
  const t = await getTranslations("auth.reset");
  const tCommon = await getTranslations("common");
  return (
    <AuthCard
      title={t("title")}
      intro={t("intro")}
      footer={
        <Link href={routes.login()} className="font-medium text-brown underline underline-offset-4">
          {tCommon("back")}
        </Link>
      }
    >
      <ForgotPasswordForm />
    </AuthCard>
  );
}
