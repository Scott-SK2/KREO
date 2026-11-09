import { defaultLocale, loadMessages } from "@kreo/i18n";
import { getRequestConfig } from "next-intl/server";

/** FR seul en V1 : pas de préfixe d'URL, locale fixée par `defaultLocale`. */
export default getRequestConfig(async () => {
  const locale = defaultLocale;
  return {
    locale,
    messages: await loadMessages(locale),
    timeZone: "Europe/Brussels",
  };
});
