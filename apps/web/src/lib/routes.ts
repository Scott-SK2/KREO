/** Routes françaises de l'application, centralisées pour éviter les chaînes dispersées. */
export const routes = {
  home: "/",
  discover: "/decouvrir",
  discoverProjects: "/decouvrir?onglet=projets",
  opportunity: (id: string) => `/annonces/${id}`,
  project: (slug: string) => `/projets/${slug}`,
  profile: (slug: string) => `/profils/${slug}`,
  register: "/inscription",
  login: (next?: string) => (next ? `/connexion?next=${encodeURIComponent(next)}` : "/connexion"),
  verifyEmail: "/verifier-email",
  forgotPassword: "/mot-de-passe-oublie",
  resetPassword: "/reinitialiser-mot-de-passe",
  onboarding: "/onboarding",
  dashboard: "/tableau-de-bord",
  applications: "/mes-candidatures",
  application: (id: string) => `/mes-candidatures/${id}`,
  messages: "/messages",
  conversation: (id: string) => `/messages/${id}`,
  notifications: "/notifications",
  account: "/compte",
  terms: "/cgu",
  privacy: "/confidentialite",
  charter: "/charte",
} as const;

/** Préfixes réservés aux membres connectés (contrôle de présence du cookie en middleware). */
export const PROTECTED_PREFIXES = [
  routes.dashboard,
  routes.onboarding,
  routes.applications,
  routes.messages,
  routes.notifications,
  routes.account,
];
