"use client";

import { Eye, EyeOff } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { TextField, type TextFieldProps } from "@/components/ui/TextField";

/** Champ mot de passe avec bouton afficher/masquer (cible 44 px, libellé accessible). */
export function PasswordField(props: Omit<TextFieldProps, "type" | "trailing">) {
  const t = useTranslations("auth.password");
  const [visible, setVisible] = useState(false);
  return (
    <TextField
      {...props}
      type={visible ? "text" : "password"}
      trailing={
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? t("hide") : t("show")}
          aria-pressed={visible}
          className="inline-flex size-11 items-center justify-center rounded-md text-taupe-dark hover:bg-ivory"
        >
          {visible ? (
            <EyeOff aria-hidden="true" className="size-5" strokeWidth={1.5} />
          ) : (
            <Eye aria-hidden="true" className="size-5" strokeWidth={1.5} />
          )}
        </button>
      }
    />
  );
}
