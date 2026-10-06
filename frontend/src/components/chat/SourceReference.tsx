"use client";

import { FileText, X } from "lucide-react";
import { useRef } from "react";

import type { SourceReference as SourceReferenceType } from "@/types/chat";

export function SourceReference({ source }: { source: SourceReferenceType }) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const pages = source.pages?.length ? source.pages : source.page == null ? [] : [source.page];
  const pageLabel = pages.length ? ` · page${pages.length > 1 ? "s" : ""} ${pages.join(", ")}` : "";
  const similarityLabel = source.similarity_percent == null ? "" : ` · ${source.similarity_percent}% match`;
  const label = `${source.file}${pageLabel}${similarityLabel}`;
  const formattedContext = (source.context ?? "")
    .split(/\n{2,}/)
    .map((paragraph) => paragraph.replace(/\s*\n\s*/g, " ").trim())
    .filter(Boolean);
  return (
    <>
      <button
        type="button"
        onClick={() => dialogRef.current?.showModal()}
        disabled={!source.context}
        title={source.context ? "View retrieved context" : "Context was not saved for this older message"}
        aria-haspopup="dialog"
        className="inline-flex items-center gap-1 rounded-lg bg-slate-100 px-2 py-1 text-left text-xs text-slate-600 transition hover:bg-amber-100 hover:text-amber-900 disabled:cursor-default disabled:hover:bg-slate-100 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-amber-950/50 dark:hover:text-amber-200 dark:disabled:hover:bg-slate-800"
      >
        <FileText size={13} />{label}
      </button>
      <dialog
        ref={dialogRef}
        aria-label={`Source context from ${label}`}
        className="fixed inset-0 m-auto max-h-[80dvh] w-[calc(100%-2rem)] max-w-2xl overflow-hidden rounded-2xl bg-white p-0 shadow-2xl backdrop:bg-slate-950/60 dark:bg-slate-900"
        onClick={(event) => {
          if (event.target === event.currentTarget) dialogRef.current?.close();
        }}
      >
        <header className="flex items-center justify-between gap-3 border-b border-slate-200 px-5 py-4 dark:border-slate-800">
          <div className="min-w-0">
            <h2 className="font-semibold text-slate-900 dark:text-white">Source context</h2>
            <p className="mt-1 break-words text-xs text-slate-500">{label}</p>
          </div>
          <button type="button" onClick={() => dialogRef.current?.close()} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800" aria-label="Close source context">
            <X size={18} />
          </button>
        </header>
        <div className="max-h-[60dvh] overflow-y-auto p-5 text-sm leading-7 text-slate-700 dark:text-slate-200">
          <div className="space-y-4 rounded-lg border-l-4 border-amber-400 bg-yellow-100 px-4 py-3 text-slate-800 dark:border-amber-500 dark:bg-yellow-950/40 dark:text-yellow-100">
            {formattedContext.map((paragraph, index) => <p key={index}>{paragraph}</p>)}
          </div>
          <p className="mt-3 text-xs text-slate-500">This is the retrieved excerpt supplied to the assistant for this answer.</p>
        </div>
      </dialog>
    </>
  );
}
