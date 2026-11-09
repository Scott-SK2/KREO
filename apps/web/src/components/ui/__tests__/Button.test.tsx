import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { Button, ButtonLink, buttonClasses } from "../Button";

describe("Button", () => {
  it("renders a button of type button by default with a 44px minimum height", () => {
    render(<Button>Enregistrer</Button>);
    const button = screen.getByRole("button", { name: "Enregistrer" });
    expect(button).toHaveAttribute("type", "button");
    expect(button.className).toContain("min-h-touch");
  });

  it("applies variant and size classes", () => {
    expect(buttonClasses("danger", "lg")).toContain("bg-bordeaux");
    expect(buttonClasses("secondary", "sm")).toContain("border-taupe");
    expect(buttonClasses("ghost")).toContain("hover:bg-ivory");
  });

  it("is disabled and announced as busy while loading", () => {
    const onClick = vi.fn();
    render(
      <Button loading onClick={onClick}>
        Envoyer
      </Button>,
    );
    const button = screen.getByRole("button", { name: "Envoyer" });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "true");
    button.click();
    expect(onClick).not.toHaveBeenCalled();
  });

  it("renders a link styled as a button", () => {
    render(<ButtonLink href="/decouvrir">Voir les annonces</ButtonLink>);
    const link = screen.getByRole("link", { name: "Voir les annonces" });
    expect(link).toHaveAttribute("href", "/decouvrir");
    expect(link.className).toContain("bg-taupe");
  });
});
