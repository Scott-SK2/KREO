import type { Metadata } from "next";
import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { Suspense } from "react";

import { AuthCard } from "@/components/auth/AuthCard";
import { RegisterForm } from "@/components/auth/RegisterForm";
import { routes } from "@/lib/routes";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("auth.register");
  return { title: t("metaTitle"), description: t("intro") };
}

export default async function RegisterPage() {
  const t = await getTranslations("auth.register");
  const tNav = await getTranslations("nav");
  return (
    <AuthCard
      title={t("title")}
      intro={t("intro")}
      footer={
        <>
          {t("haveAccount")}{" "}
          <Link
            href={routes.login()}
            className="font-medium text-brown underline underline-offset-4"
          >
            {tNav("login")}
          </Link>
        </>
      }
    >
      <Suspense>
        <RegisterForm />
      </Suspense>
    </AuthCard>
  );
}
