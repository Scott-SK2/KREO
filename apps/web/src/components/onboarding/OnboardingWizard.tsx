"use client";

import { useMutation } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useId, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { TextField } from "@/components/ui/TextField";
import { Textarea } from "@/components/ui/Textarea";
import { useToast } from "@/components/ui/Toast";
import { useErrorMessage } from "@/hooks/useErrorMessage";
import { api, unwrap } from "@/lib/api/client";
import { cn } from "@/lib/cn";
import { cityOptions, groupDisciplines, type City, type Discipline } from "@/lib/referentials";
import { routes } from "@/lib/routes";

export interface OnboardingWizardProps {
  disciplines: Discipline[];
  cities: City[];
  initial: { display_name: string; discipline_ids: number[]; city_id: number | null; bio: string };
}

const TOTAL = 3;
const MIN_DISCIPLINES = 2;

/**
 * Onboarding en trois courtes étapes : pseudonyme, disciplines (≥ 2), commune + bio
 * facultative. Un seul PATCH /me/profile à la fin, puis cap sur les annonces.
 */
export function OnboardingWizard({ disciplines, cities, initial }: OnboardingWizardProps) {
  const t = useTranslations("onboarding");
  const tCommon = useTranslations("common");
  const describeError = useErrorMessage();
  const { toast } = useToast();
  const router = useRouter();
  const id = useId();
  const [step, setStep] = useState(1);
  const [form, setForm] = useState(initial);
  const [error, setError] = useState<string | null>(null);
  const groups = groupDisciplines(disciplines);

  const save = useMutation({
    mutationFn: async () =>
      unwrap(
        await api.PATCH("/api/v1/me/profile", {
          body: {
            display_name: form.display_name.trim(),
            discipline_ids: form.discipline_ids,
            city_id: form.city_id,
            bio: form.bio.trim(),
          },
        }),
      ),
    onSuccess: () => {
      router.replace(routes.discover);
      router.refresh();
    },
    onError: (err) => toast(describeError(err), "error"),
  });

  const toggleDiscipline = (did: number) =>
    setForm((f) => ({
      ...f,
      discipline_ids: f.discipline_ids.includes(did)
        ? f.discipline_ids.filter((x) => x !== did)
        : [...f.discipline_ids, did],
    }));

  const validate = (): string | null => {
    if (step === 1 && !form.display_name.trim()) return t("displayNameRequired");
    if (step === 2 && form.discipline_ids.length < MIN_DISCIPLINES) return t("minDisciplines");
    if (step === 3 && form.city_id === null) return t("cityRequired");
    return null;
  };

  const next = (event: FormEvent) => {
    event.preventDefault();
    const problem = validate();
    setError(problem);
    if (problem) return;
    if (step < TOTAL) setStep(step + 1);
    else save.mutate();
  };

  return (
    <form onSubmit={next} noValidate className="flex flex-col gap-6">
      <div>
        <p
          className="text-xs font-medium tracking-caps text-taupe-dark uppercase"
          aria-live="polite"
        >
          {t("step", { current: step, total: TOTAL })}
        </p>
        <div
          role="progressbar"
          aria-valuemin={1}
          aria-valuemax={TOTAL}
          aria-valuenow={step}
          aria-label={t("step", { current: step, total: TOTAL })}
          className="mt-2 h-1.5 overflow-hidden rounded-full bg-ivory"
        >
          <div
            className="h-full rounded-full bg-gold transition-[width] duration-300 ease-kreo"
            style={{ width: `${(step / TOTAL) * 100}%` }}
          />
        </div>
      </div>

      {error ? (
        <p role="alert" className="text-sm font-medium text-bordeaux">
          {error}
        </p>
      ) : null}

      {step === 1 ? (
        <TextField
          id={`${id}-name`}
          label={t("displayName")}
          hint={t("displayNameHint")}
          value={form.display_name}
          onChange={(e) => setForm((f) => ({ ...f, display_name: e.target.value }))}
          autoComplete="nickname"
          maxLength={60}
          autoFocus
          required
        />
      ) : null}

      {step === 2 ? (
        <fieldset>
          <legend className="text-sm font-medium text-brown">{t("disciplines")}</legend>
          <p className="mt-1 text-sm text-taupe-dark">{t("disciplinesHint")}</p>
          <p className="mt-2 text-xs text-taupe-dark" aria-live="polite">
            {t("selected", { count: form.discipline_ids.length })}
          </p>
          <div className="mt-4 flex max-h-[50vh] flex-col gap-5 overflow-y-auto pr-1">
            {groups.map((group) => (
              <div key={group.parent?.id ?? "autres"}>
                <p className="text-xs font-medium tracking-caps text-taupe-dark uppercase">
                  {group.parent?.label ?? t("groupOther")}
                </p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {(group.parent ? [group.parent, ...group.children] : group.children).map((d) => {
                    const selected = form.discipline_ids.includes(d.id);
                    return (
                      <button
                        key={d.id}
                        type="button"
                        aria-pressed={selected}
                        onClick={() => toggleDiscipline(d.id)}
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
                  })}
                </div>
              </div>
            ))}
          </div>
        </fieldset>
      ) : null}

      {step === 3 ? (
        <div className="flex flex-col gap-5">
          <Select
            id={`${id}-city`}
            label={t("city")}
            hint={t("cityHint")}
            placeholder={t("cityPlaceholder")}
            value={form.city_id === null ? "" : String(form.city_id)}
            onChange={(e) =>
              setForm((f) => ({ ...f, city_id: e.target.value ? Number(e.target.value) : null }))
            }
            options={cityOptions(cities)}
            required
          />
          <Textarea
            id={`${id}-bio`}
            label={t("bio")}
            hint={t("bioOptional")}
            optional={tCommon("optional")}
            value={form.bio}
            onChange={(e) => setForm((f) => ({ ...f, bio: e.target.value }))}
            maxLength={600}
            rows={4}
          />
          <p className="text-xs text-taupe-dark">{t("noPhotoNeeded")}</p>
        </div>
      ) : null}

      <div className="flex items-center justify-between gap-3 border-t border-taupe/10 pt-5">
        {step > 1 ? (
          <Button variant="ghost" onClick={() => setStep(step - 1)}>
            {tCommon("back")}
          </Button>
        ) : (
          <span />
        )}
        <Button type="submit" size="lg" loading={save.isPending}>
          {step < TOTAL ? tCommon("next") : t("finish")}
        </Button>
      </div>
    </form>
  );
}
