import { ApiError } from "@kreo/api-client";
import { describe, expect, it } from "vitest";

import {
  errorFields,
  errorMessage,
  errorSlug,
  globalFieldError,
  type ErrorTranslator,
} from "../errors";

const messages: Record<string, string> = {
  "invitation-invalid": "Ce code d'invitation est invalide, déjà utilisé ou expiré.",
  "rate-limited": "Trop de requêtes. Réessaie dans un instant.",
  network: "Impossible de joindre KREO. Vérifie ta connexion.",
  unknown: "Quelque chose s'est mal passé. Réessaie.",
};

const t: ErrorTranslator = Object.assign((key: string) => messages[key] ?? `errors.${key}`, {
  has: (key: string) => key in messages,
});

const problem = (slug: string, extra: Record<string, unknown> = {}) =>
  new ApiError({
    type: `https://kreo.be/problems/${slug}`,
    title: "Erreur",
    status: 400,
    ...extra,
  });

describe("errorSlug", () => {
  it("extracts the slug of an ApiError", () => {
    expect(errorSlug(problem("invitation-invalid"))).toBe("invitation-invalid");
  });

  it("maps transport failures to network and anything else to unknown", () => {
    expect(errorSlug(new TypeError("Failed to fetch"))).toBe("network");
    expect(errorSlug(new Error("boom"))).toBe("unknown");
    expect(errorSlug(undefined)).toBe("unknown");
  });
});

describe("errorMessage", () => {
  it("translates a known slug", () => {
    expect(errorMessage(problem("rate-limited"), t)).toBe(messages["rate-limited"]);
  });

  it("falls back to errors.unknown for unknown slugs", () => {
    expect(errorMessage(problem("something-new"), t)).toBe(messages.unknown);
    expect(errorMessage(new Error("x"), t)).toBe(messages.unknown);
  });

  it("translates network errors", () => {
    expect(errorMessage(new TypeError("fetch"), t)).toBe(messages.network);
  });

  it("works without a has() helper", () => {
    const loose: ErrorTranslator = (key) => `msg:${key}`;
    expect(errorMessage(problem("role-full"), loose)).toBe("msg:role-full");
  });
});

describe("field errors", () => {
  it("indexes validation errors by field and exposes the global one", () => {
    const error = problem("validation-error", {
      errors: [
        { field: "email", message: "Adresse invalide.", code: "invalid" },
        { field: "email", message: "Doublon.", code: "unique" },
        { field: null, message: "Formulaire incomplet.", code: "incomplete" },
      ],
    });
    expect(errorFields(error)).toEqual({ email: "Adresse invalide.", _: "Formulaire incomplet." });
    expect(globalFieldError(error)).toBe("Formulaire incomplet.");
    expect(errorFields(new Error("x"))).toEqual({});
    expect(globalFieldError(new Error("x"))).toBeUndefined();
  });
});
