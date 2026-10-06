"use client";

import Link from "next/link";
import { CheckCircle2, LoaderCircle, Upload } from "lucide-react";
import { useCallback, useEffect, useRef, useState, type ChangeEvent } from "react";

import { Button } from "@/components/ui/button";
import { SessionError } from "@/services/api";
import { getDocumentIndexStatus, indexDocument, SUPPORTED_DOCUMENT_EXTENSIONS, type DocumentIndexResponse } from "@/services/documents";
import { getErrorMessage } from "@/utils/errors";

interface DocumentUploadProps {
  externalFile?: File | null;
  onExternalFileHandled?: () => void;
}

export function isSupportedDocument(file: File): boolean {
  const extension = `.${file.name.split(".").pop()?.toLowerCase()}`;
  return SUPPORTED_DOCUMENT_EXTENSIONS.some((supported) => supported === extension);
}

export function DocumentUpload({ externalFile = null, onExternalFileHandled }: DocumentUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isIndexing, setIsIndexing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [filename, setFilename] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [needsLogin, setNeedsLogin] = useState(false);

  const uploadFile = useCallback(async (file: File) => {
    if (isIndexing) return;
    setError("");
    setMessage("");
    setNeedsLogin(false);
    if (!isSupportedDocument(file)) {
      setError("Choose a PDF, TXT, DOCX, HTML, PNG, or JPG file.");
      return;
    }
    setIsIndexing(true);
    setFilename(file.name);
    setProgress(0);
    try {
      let result: DocumentIndexResponse = await indexDocument(file, setProgress);
      while (result.status === "pending" || result.status === "processing") {
        setMessage(result.status === "pending" ? "Upload complete. Waiting to start indexing…" : `Processing ${file.name} on the backend…`);
        await new Promise((resolve) => window.setTimeout(resolve, 1200));
        result = await getDocumentIndexStatus(result.job_id);
      }
      if (result.status === "failed") throw new Error(result.message ?? "Document indexing failed.");
      setMessage(`${result.filename} is ready (${result.chunks_indexed ?? 0} chunks indexed).`);
    } catch (reason) {
      setError(getErrorMessage(reason));
      setNeedsLogin(reason instanceof SessionError);
    } finally {
      setIsIndexing(false);
    }
  }, [isIndexing]);

  const handleFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    // Selecting the same file again should fire a change event.
    event.target.value = "";
    if (file) await uploadFile(file);
  };

  useEffect(() => {
    if (!externalFile) return;
    const timer = window.setTimeout(() => {
      onExternalFileHandled?.();
      void uploadFile(externalFile);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [externalFile, onExternalFileHandled, uploadFile]);

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
        {isIndexing ? "Processing document…" : "Upload document"}
      </Button>
      <p className="px-1 text-xs text-slate-500 dark:text-slate-400">PDF, TXT, DOCX, HTML, PNG, JPG</p>
      {isIndexing && <p role="status" className="break-words px-1 text-xs text-slate-500 dark:text-slate-400">{progress < 100 ? `Uploading ${filename}: ${progress}%` : `Processing ${filename}… You can keep using chat.`}</p>}
      {message && <p role="status" className="break-words rounded-xl bg-teal-50 p-3 text-xs text-teal-700 dark:bg-teal-950/40 dark:text-teal-300"><CheckCircle2 size={14} className="mb-1" />{message}</p>}
      {error && <div role="alert" className="break-words rounded-xl bg-rose-50 p-3 text-xs text-rose-700 dark:bg-rose-950/40 dark:text-rose-300">{error}{needsLogin && <Link href="/login" className="mt-2 block font-semibold underline">Sign in again</Link>}</div>}
    </section>
  );
}
