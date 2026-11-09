/** Message d'erreur global d'un formulaire, annoncé immédiatement. */
export function FormError({ message }: { message?: string | null }) {
  if (!message) return null;
  return (
    <p
      role="alert"
      className="rounded-md border border-bordeaux/30 bg-bordeaux/5 px-3 py-2 text-sm font-medium text-bordeaux"
    >
      {message}
    </p>
  );
}
