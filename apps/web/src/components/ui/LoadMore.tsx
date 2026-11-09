"use client";

import { Button } from "./Button";

export interface LoadMoreProps {
  hasMore: boolean;
  loading: boolean;
  onLoadMore: () => void;
  label: string;
  className?: string;
}

/** Pagination par curseur : un seul bouton « Voir plus », masqué en fin de liste. */
export function LoadMore({ hasMore, loading, onLoadMore, label, className }: LoadMoreProps) {
  if (!hasMore) return null;
  return (
    <div className={className ?? "mt-8 flex justify-center"}>
      <Button variant="secondary" loading={loading} onClick={onLoadMore}>
        {label}
      </Button>
    </div>
  );
}
