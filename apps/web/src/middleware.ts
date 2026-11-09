import { NextResponse, type NextRequest } from "next/server";

import { ACCESS_COOKIE } from "@/lib/api/config";
import { PROTECTED_PREFIXES, routes } from "@/lib/routes";

/**
 * Redirige les visiteurs anonymes (cookie `kreo_access` absent) vers la connexion
 * pour les pages réservées aux membres. Contrôle de présence uniquement : la
 * validité du jeton est vérifiée par l'API à chaque requête.
 */
export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const isProtected = PROTECTED_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
  if (isProtected && !request.cookies.get(ACCESS_COOKIE)) {
    const url = request.nextUrl.clone();
    url.pathname = routes.login();
    url.search = "";
    url.searchParams.set("next", `${pathname}${search}`);
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = {
  matcher: [
    "/tableau-de-bord/:path*",
    "/onboarding/:path*",
    "/mes-candidatures/:path*",
    "/messages/:path*",
    "/notifications/:path*",
    "/compte/:path*",
  ],
};
