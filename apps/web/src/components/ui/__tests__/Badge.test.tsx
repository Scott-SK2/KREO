import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CompensationBadge, StatusBadge, compensationTone } from "../Badge";

describe("CompensationBadge", () => {
  it.each([
    ["paid", "Rémunéré", "bg-gold/20"],
    ["volunteer", "Bénévole", "bg-ivory"],
    ["expenses", "Défraiement", "bg-success/15"],
    ["negotiable", "À négocier", "bg-warning/15"],
  ] as const)("renders %s with its label and tone", (compensation, label, cls) => {
    render(<CompensationBadge compensation={compensation} label={label} />);
    const badge = screen.getByText(label);
    expect(badge).toHaveAttribute("data-compensation", compensation);
    expect(badge.className).toContain(cls);
  });

  it("maps every compensation type to a tone", () => {
    expect(Object.keys(compensationTone).sort()).toEqual(
      ["expenses", "negotiable", "paid", "volunteer"].sort(),
    );
  });
});

describe("StatusBadge", () => {
  it("uses a neutral tone for unknown statuses", () => {
    render(<StatusBadge status="mystere" label="Mystère" />);
    expect(screen.getByText("Mystère").className).toContain("bg-ivory");
  });

  it("highlights accepted applications in green", () => {
    render(<StatusBadge status="accepted" label="Acceptée" />);
    expect(screen.getByText("Acceptée").className).toContain("text-success");
  });
});
