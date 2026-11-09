import { describe, expect, it } from "vitest";

import {
  DEFAULT_FILTERS,
  countActiveFilters,
  cursorFromUrl,
  parseFilters,
  parseTab,
  serializeFilters,
  toOpportunityQuery,
} from "../search-params";

describe("parseFilters", () => {
  it("returns defaults for an empty query", () => {
    expect(parseFilters(new URLSearchParams())).toEqual(DEFAULT_FILTERS);
  });

  it("reads every filter from the URL and ignores invalid values", () => {
    const params = new URLSearchParams(
      "q= théâtre &discipline=theatre,danse,theatre&commune=9&remuneration=paid,bogus,volunteer&debutants=1&tri=relevance",
    );
    expect(parseFilters(params)).toEqual({
      q: "théâtre",
      disciplines: ["theatre", "danse"],
      city: 9,
      compensation: ["paid", "volunteer"],
      beginnerFriendly: true,
      sort: "relevance",
    });
  });

  it("accepts Next.js searchParams objects", () => {
    expect(parseFilters({ commune: "abc", tri: "weird", debutants: ["1"] })).toEqual({
      ...DEFAULT_FILTERS,
      beginnerFriendly: true,
    });
    expect(parseFilters({ commune: ["12"] }).city).toBe(12);
  });
});

describe("serializeFilters", () => {
  it("omits default values and the default tab", () => {
    expect(serializeFilters(DEFAULT_FILTERS)).toBe("");
    expect(serializeFilters({ sort: "recent" }, "annonces")).toBe("");
  });

  it("round-trips through parseFilters", () => {
    const filters = {
      q: "clip",
      disciplines: ["clip", "musique"],
      city: 15,
      compensation: ["negotiable" as const],
      beginnerFriendly: true,
      sort: "relevance" as const,
    };
    const qs = serializeFilters(filters, "projets");
    const params = new URLSearchParams(qs);
    expect(parseTab(params)).toBe("projets");
    expect(parseFilters(params)).toEqual(filters);
  });
});

describe("helpers", () => {
  it("counts active filters excluding search and sort", () => {
    expect(countActiveFilters(DEFAULT_FILTERS)).toBe(0);
    expect(
      countActiveFilters({
        ...DEFAULT_FILTERS,
        q: "x",
        sort: "relevance",
        city: 4,
        beginnerFriendly: true,
      }),
    ).toBe(2);
  });

  it("builds the API query without empty values", () => {
    expect(toOpportunityQuery(DEFAULT_FILTERS)).toEqual({
      q: undefined,
      discipline: undefined,
      city: undefined,
      compensation: undefined,
      beginner_friendly: undefined,
      sort: undefined,
    });
    expect(
      toOpportunityQuery({ ...DEFAULT_FILTERS, disciplines: ["danse"], city: 4 }),
    ).toMatchObject({
      discipline: "danse",
      city: "4",
    });
  });

  it("extracts the cursor from a next URL", () => {
    expect(cursorFromUrl("http://localhost:8000/api/v1/opportunities?cursor=cD00ODY%3D")).toBe(
      "cD00ODY=",
    );
    expect(cursorFromUrl(null)).toBeUndefined();
    expect(cursorFromUrl("::not a url::")).toBeUndefined();
  });

  it("falls back to the opportunities tab", () => {
    expect(parseTab(new URLSearchParams("onglet=inconnu"))).toBe("annonces");
    expect(parseTab(new URLSearchParams("onglet=createurs"))).toBe("createurs");
  });
});
