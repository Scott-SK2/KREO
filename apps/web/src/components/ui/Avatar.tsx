import { cn } from "@/lib/cn";
import { initials } from "@/lib/format";

export interface AvatarProps {
  name: string;
  /** URL d'image facultative : KREO n'impose jamais de photo. */
  src?: string | null;
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
}

const sizes = {
  sm: "size-8 text-xs",
  md: "size-10 text-sm",
  lg: "size-14 text-base",
  xl: "size-20 text-xl",
};

/** Avatar avec repli sur les initiales, fond ivoire et lettrage brun. */
export function Avatar({ name, src, size = "md", className }: AvatarProps) {
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-ivory font-display font-black text-brown ring-1 ring-taupe/20",
        sizes[size],
        className,
      )}
      role="img"
      aria-label={name}
    >
      {src ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={src} alt="" className="size-full object-cover" />
      ) : (
        <span aria-hidden="true">{initials(name)}</span>
      )}
    </span>
  );
}
