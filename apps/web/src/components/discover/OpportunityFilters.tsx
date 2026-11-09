"use client";

import { SlidersHorizontal, X } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useId, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Checkbox } from "@/components/ui/Checkbox";
import { Select } from "@/components/ui/Select";
import { TextField } from "@/components/ui/TextField";
import { cn } from "@/lib/cn";
import { cityOptions, groupDisciplines, type City, type Discipline } from "@/lib/referentials";
import {
  COMPENSATIONS,
  DEFAULT_FILTERS,
  countActiveFilters,
  type Compensation,
  type OpportunityFilters as Filters,
} from "@/lib/search-params";

export interface OpportunityFiltersProps {
  filters: Filters;
  onChange: (filters: Filters) => void;
  disciplines: Discipline[];
  cities: City[];
}

/**
 * Filtres des annonces : recherche, disciplines (puces groupées par parent),
 * commune, rémunération, débutants, tri. Chaque changement remonte au parent
 * qui synchronise l'URL.
 */
export function OpportunityFilters({
  filters,
  onChange,
  disciplines,
  cities,
}: OpportunityFiltersProps) {
  const t = useTranslations("discover");
  const tComp = useTranslations("compensation");
  const id = useId();
  const [q, setQ] = useState(filters.q);
  const [open, setOpen] = useState(false);
  const groups = groupDisciplines(disciplines);
  const active = countActiveFilters(filters);

  // Recherche textuelle : on attend 350 ms de pause avant d'interroger l'API.
  useEffect(() => {
    if (q === filters.q) return;
    const timer = window.setTimeout(() => onChange({ ...filters, q }), 350);
    return () => window.clearTimeout(timer);
  }, [q, filters, onChange]);

  useEffect(() => {
    setQ(filters.q);
  }, [filters.q]);

  const toggleDiscipline = (slug: string) => {
    const set = new Set(filters.disciplines);
    if (set.has(slug)) set.delete(slug);
    else set.add(slug);
    onChange({ ...filters, disciplines: Array.from(set) });
  };

  const toggleCompensation = (value: Compensation) => {
    const set = new Set(filters.compensation);
    if (set.has(value)) set.delete(value);
    else set.add(value);
    onChange({ ...filters, compensation: Array.from(set) });
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="grid gap-3 sm:grid-cols-[1fr_auto_auto] sm:items-end">
        <TextField
          id={`${id}-q`}
          type="search"
          label={t("search")}
          placeholder={t("searchPlaceholder")}
          value={q}
          onChange={(e) => setQ(e.target.value)}
          autoComplete="off"
        />
        <Select
          id={`${id}-sort`}
          label={t("sort")}
          value={filters.sort}
          onChange={(e) => onChange({ ...filters, sort: e.target.value as Filters["sort"] })}
          options={[
            { value: "recent", label: t("sortRecent") },
            { value: "relevance", label: t("sortRelevance") },
          ]}
        />
        <Button
          variant="secondary"
          icon={<SlidersHorizontal aria-hidden="true" className="size-4" strokeWidth={1.5} />}
          aria-expanded={open}
          aria-controls={`${id}-panel`}
          onClick={() => setOpen((v) => !v)}
          className="sm:self-end"
        >
          {open ? t("closeFilters") : t("openFilters")}
          {active ? (
            <span className="rounded-full bg-gold/30 px-2 py-0.5 text-xs text-brown">{active}</span>
          ) : null}
        </Button>
      </div>

      <div
        id={`${id}-panel`}
        hidden={!open}
        className={cn("rounded-xl border border-taupe/15 bg-white p-4 sm:p-5")}
      >
        <div className="grid gap-6 md:grid-cols-[2fr_1fr]">
          <fieldset>
            <legend className="text-sm font-medium text-brown">{t("discipline")}</legend>
            <div className="mt-3 flex flex-col gap-4">
              {groups.map((group) => (
                <div key={group.parent?.id ?? "autres"}>
                  <p className="text-xs font-medium tracking-caps text-taupe-dark uppercase">
                    {group.parent?.label ?? "—"}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {(group.parent ? [group.parent, ...group.children] : group.children).map(
                      (d) => {
                        const selected = filters.disciplines.includes(d.slug);
                        return (
                          <button
                            key={d.id}
                            type="button"
                            aria-pressed={selected}
                            onClick={() => toggleDiscipline(d.slug)}
                            className={cn(
                              "min-h-touch rounded-full border px-3 text-sm transition-colors",
                              selected
                                ? "border-brown bg-brown text-paper"
                                : "border-taupe/40 text-brown hover:bg-ivory",
                            )}
                          >
                            {d.label}
                          </button>
                        );
                      },
                    )}
                  </div>
                </div>
              ))}
            </div>
          </fieldset>

          <div className="flex flex-col gap-5">
            <Select
              id={`${id}-city`}
              label={t("city")}
              placeholder={t("allCities")}
              value={filters.city === null ? "" : String(filters.city)}
              onChange={(e) =>
                onChange({ ...filters, city: e.target.value ? Number(e.target.value) : null })
              }
              options={cityOptions(cities)}
            />
            <fieldset>
              <legend className="text-sm font-medium text-brown">{t("compensation")}</legend>
              <div className="mt-1 flex flex-col">
                {COMPENSATIONS.map((c) => (
                  <Checkbox
                    key={c}
                    id={`${id}-comp-${c}`}
                    label={tComp(c)}
                    checked={filters.compensation.includes(c)}
                    onChange={() => toggleCompensation(c)}
                  />
                ))}
              </div>
            </fieldset>
            <Checkbox
              id={`${id}-beginner`}
              label={t("beginnerFriendly")}
              checked={filters.beginnerFriendly}
              onChange={(e) => onChange({ ...filters, beginnerFriendly: e.target.checked })}
            />
          </div>
        </div>
        <div className="mt-4 flex justify-end border-t border-taupe/10 pt-4">
          <Button
            variant="ghost"
            size="sm"
            icon={<X aria-hidden="true" className="size-4" strokeWidth={1.5} />}
            onClick={() => {
              setQ("");
              onChange({ ...DEFAULT_FILTERS });
            }}
          >
            {t("reset")}
          </Button>
        </div>
      </div>
    </div>
  );
}
