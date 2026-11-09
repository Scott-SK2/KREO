import fr from "./locales/fr.json";

export type Locale = "fr" | "nl" | "en";
export const locales: Locale[] = ["fr", "nl", "en"];
export const defaultLocale: Locale = "fr";
export type Messages = typeof fr;

export { fr };

export async function loadMessages(locale: Locale): Promise<Messages> {
  switch (locale) {
    case "nl":
      return (await import("./locales/nl.json")).default as Messages;
    case "en":
      return (await import("./locales/en.json")).default as Messages;
    default:
      return fr;
  }
}

/** Formatage fr-BE des dates et nombres (exigence non fonctionnelle). */
export const formatters = {
  date: (locale: Locale = "fr") =>
    new Intl.DateTimeFormat(`${locale}-BE`, {
      day: "numeric",
      month: "long",
      year: "numeric",
      timeZone: "Europe/Brussels",
    }),
  dateTime: (locale: Locale = "fr") =>
    new Intl.DateTimeFormat(`${locale}-BE`, {
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "Europe/Brussels",
    }),
  number: (locale: Locale = "fr") => new Intl.NumberFormat(`${locale}-BE`),
};
