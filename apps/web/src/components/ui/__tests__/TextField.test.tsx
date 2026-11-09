import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TextField } from "../TextField";

describe("TextField", () => {
  it("links the label, hint and error to the input", () => {
    render(
      <TextField
        id="email"
        label="Adresse e-mail"
        hint="Nous ne la partageons jamais."
        error="Un compte existe déjà avec cet e-mail."
        defaultValue=""
      />,
    );
    const input = screen.getByLabelText("Adresse e-mail");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAttribute("aria-describedby", "email-hint email-error");
    expect(screen.getByText("Nous ne la partageons jamais.")).toHaveAttribute("id", "email-hint");
    const error = screen.getByRole("alert");
    expect(error).toHaveAttribute("id", "email-error");
    expect(error).toHaveTextContent("Un compte existe déjà avec cet e-mail.");
  });

  it("has no aria-invalid nor describedby without hint or error", () => {
    render(<TextField id="code" label="Code d'invitation" defaultValue="" />);
    const input = screen.getByLabelText("Code d'invitation");
    expect(input).not.toHaveAttribute("aria-invalid");
    expect(input).not.toHaveAttribute("aria-describedby");
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("shows the optional marker", () => {
    render(<TextField id="bio" label="Bio" optional="facultatif" defaultValue="" />);
    expect(screen.getByText("(facultatif)")).toBeInTheDocument();
  });
});
