/** Erreur API au format RFC 9457 (application/problem+json). */
export interface Problem {
  type: string;
  title: string;
  status: number;
  detail?: string;
  instance?: string;
  errors?: { field: string | null; message: string; code: string }[];
  [key: string]: unknown;
}

export const PROBLEM_TYPE_BASE = "https://kreo.be/problems/";

export function isProblem(value: unknown): value is Problem {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as Problem).type === "string" &&
    typeof (value as Problem).status === "number"
  );
}

/** Slug stable du problème (ex. "invitation-invalid"), utilisé comme clé i18n `errors.<slug>`. */
export function problemSlug(problem: Problem | undefined | null): string {
  if (!problem) return "unknown";
  return problem.type.startsWith(PROBLEM_TYPE_BASE)
    ? problem.type.slice(PROBLEM_TYPE_BASE.length)
    : problem.type;
}

/** Erreurs de validation indexées par champ. */
export function fieldErrors(problem: Problem | undefined | null): Record<string, string> {
  const out: Record<string, string> = {};
  for (const err of problem?.errors ?? []) {
    const key = err.field ?? "_";
    if (!(key in out)) out[key] = err.message;
  }
  return out;
}

export class ApiError extends Error {
  readonly problem: Problem;
  readonly status: number;

  constructor(problem: Problem) {
    super(problem.detail ?? problem.title);
    this.name = "ApiError";
    this.problem = problem;
    this.status = problem.status;
  }

  get slug(): string {
    return problemSlug(this.problem);
  }
}
