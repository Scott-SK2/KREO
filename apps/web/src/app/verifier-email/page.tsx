import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { Suspense } from "react";

import { AuthCard } from "@/components/auth/AuthCard";
import { VerifyEmail } from "@/components/auth/VerifyEmail";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("auth.verifyEmail");
  return { title: t("title"), robots: { index: false } };
}

export default async function VerifyEmailPage() {
  const t = await getTranslations("auth.verifyEmail");
  return (
    <AuthCard title={t("title")}>
      <Suspense>
        <VerifyEmail />
      </Suspense>
    </AuthCard>
  );
}
