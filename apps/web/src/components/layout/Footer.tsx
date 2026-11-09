import Link from "next/link";
import { getTranslations } from "next-intl/server";

import { Logo } from "@/components/ui/Logo";
import { routes } from "@/lib/routes";

/** Pied de page : mentions légales, contact et signature Genius Harmony. */
export async function Footer() {
  const t = await getTranslations("footer");
  const tBrand = await getTranslations("brand");
  const links = [
    { href: routes.terms, label: t("terms") },
    { href: routes.privacy, label: t("privacy") },
    { href: routes.charter, label: t("charter") },
    { href: "mailto:bonjour@kreo.be", label: t("contact") },
  ];
  return (
    <footer className="mt-16 border-t border-taupe/15 bg-ivory/60">
      <div className="kreo-container flex flex-col gap-6 py-10 md:flex-row md:items-start md:justify-between">
        <div className="max-w-sm">
          <Logo height={22} />
          <p className="mt-3 text-sm text-taupe-dark">{tBrand("support")}</p>
        </div>
        <nav aria-label={t("terms")}>
          <ul className="flex flex-wrap gap-x-6 gap-y-2">
            {links.map((link) => (
              <li key={link.href}>
                <Link
                  href={link.href}
                  className="inline-flex min-h-touch items-center text-sm text-brown underline-offset-4 hover:underline"
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </div>
      <div className="kreo-container border-t border-taupe/10 py-4">
        <p className="text-xs text-taupe-dark">{t("madeIn")}</p>
      </div>
    </footer>
  );
}
