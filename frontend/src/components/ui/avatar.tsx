interface AvatarProps { name?: string | null; className?: string; }

export function Avatar({ name, className = "" }: AvatarProps) {
  const initial = name?.trim().charAt(0).toUpperCase() || "U";
  return <div aria-hidden="true" className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-teal-100 text-sm font-bold text-teal-700 dark:bg-teal-950 dark:text-teal-300 ${className}`}>{initial}</div>;
}
