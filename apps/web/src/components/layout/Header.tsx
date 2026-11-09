import Link from "next/link";
import { getTranslations } from "next-intl/server";

import { ButtonLink } from "@/components/ui/Button";
import { Logo } from "@/components/ui/Logo";
import { orNull, serverApi, unwrap } from "@/lib/api/server";
import { getCurrentUser } from "@/lib/auth";
import { routes } from "@/lib/routes";

import { MobileNav } from "./MobileNav";
import { UserMenu } from "./UserMenu";

/** En-tête : logo, navigation publique, connexion/inscription ou menu du membre. */
export async function Header() {
  const t = await getTranslations("nav");
  const user = await getCurrentUser();
  let displayName = user?.email.split("@")[0] ?? "";
  if (user) {
    const api = await serverApi();
    const profile = await orNull(api.GET("/api/v1/me/profile").then(unwrap));
    if (profile?.display_name) displayName = profile.display_name;
  }

  const links = [
    { href: routes.discover, label: t("discover") },
    { href: routes.discoverProjects, label: t("projects") },
    { href: `${routes.discover}?onglet=createurs`, label: t("creators") },
  ];

  return (
    <header className="relative z-30 border-b border-taupe/15 bg-paper/95 backdrop-blur">
      <div className="kreo-container flex min-h-16 items-center justify-between gap-4">
        <div className="flex items-center gap-6">
          <Link href={routes.home} className="flex min-h-touch items-center rounded-md px-1">
            <Logo height={26} />
          </Link>
          <nav aria-label={t("discover")} className="hidden md:block">
            <ul className="flex items-center gap-1">
              {links.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="inline-flex min-h-touch items-center rounded-md px-3 text-sm font-medium text-brown hover:bg-ivory"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>
        <div className="flex items-center gap-2">
          {user ? (
            <UserMenu user={user} displayName={displayName} />
          ) : (
            <>
              <ButtonLink href={routes.login()} variant="ghost" size="sm">
                {t("login")}
              </ButtonLink>
              <ButtonLink href={routes.register} size="sm" className="hidden sm:inline-flex">
                {t("register")}
              </ButtonLink>
            </>
          )}
          <MobileNav links={links} />
        </div>
      </div>
    </header>
  );
}
