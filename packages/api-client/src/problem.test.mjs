import { test } from "node:test";
import assert from "node:assert/strict";

// Les helpers sont testés via une copie JS minimale du module TS (pas de transpilation dans ce paquet).
const BASE = "https://kreo.be/problems/";
const problemSlug = (p) =>
  p ? (p.type.startsWith(BASE) ? p.type.slice(BASE.length) : p.type) : "unknown";
const fieldErrors = (p) =>
  Object.fromEntries((p?.errors ?? []).map((e) => [e.field ?? "_", e.message]));

test("slug stable depuis le type", () => {
  assert.equal(
    problemSlug({ type: `${BASE}invitation-invalid`, title: "x", status: 422 }),
    "invitation-invalid",
  );
  assert.equal(problemSlug(undefined), "unknown");
});

test("erreurs par champ", () => {
  const p = {
    type: `${BASE}validation-error`,
    title: "x",
    status: 400,
    errors: [{ field: "email", message: "Invalide", code: "invalid" }],
  };
  assert.deepEqual(fieldErrors(p), { email: "Invalide" });
});
