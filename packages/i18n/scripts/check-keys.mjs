// Contrôle : toutes les clés FR existent dans NL et EN (valeur vide tolérée tant que la langue n'est pas lancée).
import { readFileSync } from "node:fs";

const load = (l) =>
  JSON.parse(readFileSync(new URL(`../src/locales/${l}.json`, import.meta.url), "utf8"));
const flatten = (obj, prefix = "") =>
  Object.entries(obj).flatMap(([k, v]) =>
    typeof v === "object" && v !== null ? flatten(v, `${prefix}${k}.`) : [`${prefix}${k}`],
  );

const fr = new Set(flatten(load("fr")));
let errors = 0;
for (const locale of ["nl", "en"]) {
  const keys = new Set(flatten(load(locale)));
  for (const k of fr)
    if (!keys.has(k)) {
      console.error(`[${locale}] clé manquante : ${k}`);
      errors++;
    }
  for (const k of keys)
    if (!fr.has(k)) {
      console.error(`[${locale}] clé orpheline : ${k}`);
      errors++;
    }
}
if (errors) process.exit(1);
console.log(`i18n OK : ${fr.size} clés alignées sur fr, nl, en.`);
