"use client";

import { Menu, X } from "lucide-react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useId, useState } from "react";

export interface NavLink {
  href: string;
  label: string;
}

/** Navigation repliée sur mobile : bouton ≥ 44 px, liste simple, fermeture au clic. */
export function MobileNav({ links }: { links: NavLink[] }) {
  const t = useTranslations("common");
  const [open, setOpen] = useState(false);
  const id = useId();
  return (
    <div className="md:hidden">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={id}
        aria-label={open ? t("closeMenu") : t("openMenu")}
        onClick={() => setOpen((v) => !v)}
        className="inline-flex size-11 items-center justify-center rounded-md text-brown hover:bg-ivory"
      >
        {open ? (
          <X aria-hidden="true" className="size-5" strokeWidth={1.5} />
        ) : (
          <Menu aria-hidden="true" className="size-5" strokeWidth={1.5} />
        )}
      </button>
      <nav
        id={id}
        hidden={!open}
        aria-label={t("menu")}
        className="absolute inset-x-0 top-full border-b border-taupe/20 bg-paper shadow-md"
      >
        <ul className="kreo-container flex flex-col py-2">
          {links.map((link) => (
            <li key={link.href}>
              <Link
                href={link.href}
                onClick={() => setOpen(false)}
                className="flex min-h-touch items-center px-2 text-base font-medium text-brown hover:bg-ivory"
              >
                {link.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}
