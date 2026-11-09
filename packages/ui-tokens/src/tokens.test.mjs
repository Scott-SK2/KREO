import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const tokens = JSON.parse(readFileSync(new URL("./tokens.json", import.meta.url), "utf8"));

function luminance(hex) {
  const [r, g, b] = [1, 3, 5]
    .map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
function contrast(a, b) {
  const [l1, l2] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (l1 + 0.05) / (l2 + 0.05);
}

test("couleurs de la charte présentes", () => {
  assert.equal(tokens.color.taupe.value, "#8B7262");
  assert.equal(tokens.color.ink.value, "#16110E");
  assert.equal(tokens.color.gold.value, "#C6A15B");
  assert.equal(tokens.color.bordeaux.value, "#7B2D3B");
});

test("contraste AA (≥ 4.5) pour le texte sur fond papier et ivoire", () => {
  for (const bg of ["paper", "ivory", "white"]) {
    for (const fg of ["ink", "brown", "taupe-dark", "bordeaux", "success", "warning"]) {
      const ratio = contrast(tokens.color[fg].value, tokens.color[bg].value);
      assert.ok(ratio >= 4.5, `${fg} sur ${bg} : ${ratio.toFixed(2)}`);
    }
  }
});

test("contraste AA du texte clair sur encre et taupe foncé", () => {
  assert.ok(contrast(tokens.color.paper.value, tokens.color.ink.value) >= 4.5);
  assert.ok(contrast(tokens.color.white.value, tokens.color["taupe-dark"].value) >= 4.5);
  assert.ok(contrast(tokens.color.white.value, tokens.color.bordeaux.value) >= 4.5);
});
