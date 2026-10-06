"use client";

import Link from "next/link";
import { CheckCircle2, LoaderCircle, Upload } from "lucide-react";
import { useRef, useState, type ChangeEvent } from "react";

import { Button } from "@/components/ui/button";
import { SessionError } from "@/services/api";
import { indexDocument, SUPPORTED_DOCUMENT_EXTENSIONS } from "@/services/documents";
import { getErrorMessage } from "@/utils/errors";

export function DocumentUpload() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isIndexing, setIsIndexing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [filename, setFilename] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [needsLogin, setNeedsLogin] = useState(false);

  const handleFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    // Selecting the same file again should fire a change event.
    event.target.value = "";
    if (!file || isIndexing) return;
    setError("");
    setMessage("");
    setNeedsLogin(false);
    const extension = `.${file.name.split(".").pop()?.toLowerCase()}`;
    if (!SUPPORTED_DOCUMENT_EXTENSIONS.some((supported) => supported === extension)) {
      setError("Choose a PDF, TXT, DOCX, HTML, PNG, or JPG file.");
      return;
    }
    setIsIndexing(true);
    setFilename(file.name);
    setProgress(0);
    try {
      const result = await indexDocument(file, setProgress);
      setMessage(`${result.filename} is ready (${result.chunks_indexed} chunks indexed).`);
    } catch (reason) {
      setError(getErrorMessage(reason));
      setNeedsLogin(reason instanceof SessionError);
    } finally {
      setIsIndexing(false);
    }
  };

  return (
    <section aria-label="Upload knowledge-base documents" className="mt-6 space-y-2">
      <input
        ref={inputRef}
        type="file"
        accept={SUPPORTED_DOCUMENT_EXTENSIONS.join(",")}
        onChange={handleFile}
        disabled={isIndexing}
        className="sr-only"
        tabIndex={-1}
        aria-label="Choose a knowledge-base document"
      />
      <Button variant="secondary" className="w-full justify-start gap-2" disabled={isIndexing} onClick={() => inputRef.current?.click()}>
        {isIndexing ? <LoaderCircle size={17} className="animate-spin" /> : <Upload size={17} />}
        {isIndexing ? "Indexing document…" : "Upload document"}
      </Button>
      <p className="px-1 text-xs text-slate-500 dark:text-slate-400">PDF, TXT, DOCX, HTML, PNG, JPG</p>
      {isIndexing && <p role="status" className="break-words px-1 text-xs text-slate-500 dark:text-slate-400">{progress < 100 ? `Uploading ${filename}: ${progress}%` : `Processing ${filename}… This may take a few minutes.`}</p>}
      {message && <p role="status" className="break-words rounded-xl bg-teal-50 p-3 text-xs text-teal-700 dark:bg-teal-950/40 dark:text-teal-300"><CheckCircle2 size={14} className="mb-1" />{message}</p>}
      {error && <div role="alert" className="break-words rounded-xl bg-rose-50 p-3 text-xs text-rose-700 dark:bg-rose-950/40 dark:text-rose-300">{error}{needsLogin && <Link href="/login" className="mt-2 block font-semibold underline">Sign in again</Link>}</div>}
    </section>
  );
}
