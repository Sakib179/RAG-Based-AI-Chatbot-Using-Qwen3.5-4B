import { FileText } from "lucide-react";

import type { SourceReference as SourceReferenceType } from "@/types/chat";

export function SourceReference({ source }: { source: SourceReferenceType }) {
  return <span className="inline-flex items-center gap-1 rounded-lg bg-slate-100 px-2 py-1 text-xs text-slate-600 dark:bg-slate-800 dark:text-slate-300"><FileText size={13} />{source.file}{source.page ? ` · page ${source.page}` : ""}</span>;
}
