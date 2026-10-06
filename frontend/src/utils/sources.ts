import type { SourceReference } from "@/types/chat";

/** Collapse duplicate source records from older persisted assistant messages. */
export function mergeSourceReferences(sources: SourceReference[]): SourceReference[] {
  const grouped = new Map<string, SourceReference>();
  for (const source of sources) {
    const existing = grouped.get(source.file);
    if (!existing) {
      grouped.set(source.file, {
        ...source,
        pages: [...new Set(source.pages ?? (source.page == null ? [] : [source.page]))].sort((a, b) => a - b),
      });
      continue;
    }
    const pages = [
      ...(existing.pages ?? []),
      ...(source.pages ?? (source.page == null ? [] : [source.page])),
    ];
    existing.pages = [...new Set(pages)].sort((a, b) => a - b);
    if ((source.similarity_percent ?? 0) > (existing.similarity_percent ?? 0)) {
      existing.similarity_percent = source.similarity_percent;
    }
    if (source.context && !existing.context?.includes(source.context)) {
      existing.context = [existing.context, source.context].filter(Boolean).join("\n\n");
    }
  }
  return [...grouped.values()];
}
