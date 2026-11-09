import type { components } from "@kreo/api-client";

export type Discipline = components["schemas"]["Discipline"];
export type City = components["schemas"]["City"];

export interface DisciplineGroup {
  parent: Discipline | null;
  children: Discipline[];
}

/** Regroupe les disciplines par parent (les parents en tête, triés par libellé). */
export function groupDisciplines(disciplines: Discipline[]): DisciplineGroup[] {
  const active = disciplines.filter((d) => d.active !== false);
  const parents = active
    .filter((d) => d.parent_id === null)
    .sort((a, b) => a.label.localeCompare(b.label, "fr"));
  const groups: DisciplineGroup[] = parents.map((parent) => ({
    parent,
    children: active
      .filter((d) => d.parent_id === parent.id)
      .sort((a, b) => a.label.localeCompare(b.label, "fr")),
  }));
  const orphans = active.filter(
    (d) => d.parent_id !== null && !parents.some((p) => p.id === d.parent_id),
  );
  if (orphans.length) groups.push({ parent: null, children: orphans });
  return groups.filter((g) => g.children.length > 0 || g.parent);
}

/** Options de communes triées par libellé. */
export function cityOptions(cities: City[]) {
  return [...cities]
    .sort((a, b) => a.label.localeCompare(b.label, "fr"))
    .map((c) => ({ value: String(c.id), label: `${c.label} (${c.postal_code})` }));
}
