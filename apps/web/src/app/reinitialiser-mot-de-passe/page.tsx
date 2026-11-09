import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { Suspense } from "react";

import { AuthCard } from "@/components/auth/AuthCard";
import { ResetPasswordForm } from "@/components/auth/ResetPasswordForm";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("auth.reset");
  return { title: t("newPassword"), robots: { index: false } };
}

export default async function ResetPasswordPage() {
  const t = await getTranslations("auth.reset");
  return (
    <AuthCard title={t("newPassword")}>
      <Suspense>
        <ResetPasswordForm />
      </Suspense>
    </AuthCard>
  );
}
