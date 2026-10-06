import { api } from "@/services/api";

export const SUPPORTED_DOCUMENT_EXTENSIONS = [
  ".pdf", ".txt", ".docx", ".html", ".htm", ".png", ".jpg", ".jpeg",
] as const;

export type DocumentJobStatus = "pending" | "processing" | "completed" | "failed";

export interface DocumentIndexResponse {
  job_id: string;
  status: DocumentJobStatus;
  filename: string;
  chunks_indexed: number | null;
  source: string;
  document_id: string | null;
  message?: string | null;
}

export async function indexDocument(
  file: File,
  onProgress?: (percent: number) => void,
): Promise<DocumentIndexResponse> {
  const body = new FormData();
  body.append("file", file);
  const response = await api.post<DocumentIndexResponse>("/api/documents/index", body, {
    onUploadProgress: ({ loaded, total }) => {
      if (total) onProgress?.(Math.round((loaded / total) * 100));
    },
  });
  return response.data;
}

export async function getDocumentIndexStatus(jobId: string): Promise<DocumentIndexResponse> {
  const response = await api.get<DocumentIndexResponse>(`/api/documents/index/${encodeURIComponent(jobId)}`);
  return response.data;
}
