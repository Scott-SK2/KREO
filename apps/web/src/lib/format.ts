import { formatters } from "@kreo/i18n";

const dateFormatter = formatters.date("fr");
const dateTimeFormatter = formatters.dateTime("fr");

/** « 9 novembre 2026 » */
export function formatDate(value: string | null | undefined): string {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : dateFormatter.format(date);
}

/** « 9 nov., 14:26 » */
export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : dateTimeFormatter.format(date);
}

/** Initiales (deux lettres max) à partir d'un nom d'affichage. */
export function initials(name: string | null | undefined): string {
  if (!name) return "K";
  const parts = name.trim().split(/\s+/).filter(Boolean);
  const letters = parts.slice(0, 2).map((p) => p[0]?.toUpperCase() ?? "");
  return letters.join("") || "K";
}

/** Libellé lisible d'une valeur de critère (liste, texte, nombre, intervalle). */
export function requirementValue(value: unknown): string {
  if (Array.isArray(value)) return value.map((v) => requirementValue(v)).join(", ");
  if (value && typeof value === "object") {
    const obj = value as Record<string, unknown>;
    if ("min" in obj || "max" in obj) return [obj.min, obj.max].filter((v) => v != null).join(" – ");
    return Object.values(obj).map((v) => requirementValue(v)).join(", ");
  }
  if (typeof value === "boolean") return value ? "oui" : "non";
  return value == null ? "" : String(value);
}
