import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { AuthCard } from "@/components/auth/AuthCard";
import { OnboardingWizard } from "@/components/onboarding/OnboardingWizard";
import { orNull, publicApi, serverApi, unwrap } from "@/lib/api/server";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("onboarding");
  return { title: t("title"), robots: { index: false } };
}

export default async function OnboardingPage() {
  const t = await getTranslations("onboarding");
  const publicClient = publicApi(3600);
  const api = await serverApi();
  const [disciplines, cities, profile] = await Promise.all([
    publicClient
      .GET("/api/v1/disciplines")
      .then(unwrap)
      .catch(() => []),
    publicClient
      .GET("/api/v1/cities")
      .then(unwrap)
      .catch(() => []),
    orNull(api.GET("/api/v1/me/profile").then(unwrap)),
  ]);

  return (
    <AuthCard title={t("title")}>
      <OnboardingWizard
        disciplines={disciplines}
        cities={cities}
        initial={{
          display_name: profile?.display_name ?? "",
          discipline_ids: profile?.disciplines.map((d) => d.id) ?? [],
          city_id: profile?.city?.id ?? null,
          bio: profile?.bio ?? "",
        }}
      />
    </AuthCard>
  );
}
