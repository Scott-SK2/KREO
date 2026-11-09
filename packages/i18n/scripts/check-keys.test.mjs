import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";

test("les trois locales ont les mêmes clés", () => {
  const out = execFileSync(process.execPath, [
    new URL("./check-keys.mjs", import.meta.url).pathname,
  ]).toString();
  assert.match(out, /i18n OK/);
});
