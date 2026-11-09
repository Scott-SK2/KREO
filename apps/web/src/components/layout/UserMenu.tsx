"use client";

import { Bell, ChevronDown, LayoutDashboard, LogOut, Mail, Send, UserRound } from "lucide-react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useEffect, useId, useRef, useState } from "react";

import { Avatar } from "@/components/ui/Avatar";
import { useLogout, type Me } from "@/hooks/useMe";
import { cn } from "@/lib/cn";
import { routes } from "@/lib/routes";

/** Menu du membre connecté : liens privés et déconnexion, fermeture au clic extérieur et Échap. */
export function UserMenu({ user, displayName }: { user: Me; displayName: string }) {
  const t = useTranslations("nav");
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const menuId = useId();
  const logout = useLogout();

  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const items = [
    { href: routes.dashboard, label: t("dashboard"), icon: LayoutDashboard },
    { href: routes.applications, label: t("myApplications"), icon: Send },
    { href: routes.messages, label: t("messages"), icon: Mail },
    { href: routes.notifications, label: t("notifications"), icon: Bell },
    { href: routes.account, label: t("account"), icon: UserRound },
  ];

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={menuId}
        aria-label={t("userMenu")}
        onClick={() => setOpen((v) => !v)}
        className="flex min-h-touch items-center gap-2 rounded-full py-1 pr-2 pl-1 hover:bg-ivory"
      >
        <Avatar name={displayName} size="sm" />
        <span className="hidden max-w-32 truncate text-sm font-medium text-brown sm:inline">
          {displayName}
        </span>
        <ChevronDown aria-hidden="true" className="size-4 text-taupe-dark" strokeWidth={1.5} />
      </button>
      <div
        id={menuId}
        role="menu"
        hidden={!open}
        className={cn(
          "absolute right-0 z-40 mt-2 w-60 overflow-hidden rounded-xl border border-taupe/20 bg-white py-2 shadow-lg",
        )}
      >
        <p className="truncate px-4 py-2 text-xs text-taupe-dark">{user.email}</p>
        {items.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            role="menuitem"
            href={href}
            onClick={() => setOpen(false)}
            className="flex min-h-touch items-center gap-3 px-4 text-sm text-brown hover:bg-ivory"
          >
            <Icon aria-hidden="true" className="size-4 text-taupe-dark" strokeWidth={1.5} />
            {label}
          </Link>
        ))}
        <button
          type="button"
          role="menuitem"
          onClick={() => void logout()}
          className="flex min-h-touch w-full items-center gap-3 px-4 text-left text-sm text-brown hover:bg-ivory"
        >
          <LogOut aria-hidden="true" className="size-4 text-taupe-dark" strokeWidth={1.5} />
          {t("logout")}
        </button>
      </div>
    </div>
  );
}
