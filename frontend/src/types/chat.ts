export interface SourceReference {
  file: string;
  pages?: number[];
  similarity_percent?: number;
  // Legacy fields are kept so previously persisted messages remain readable.
  page?: number | null;
  context?: string | null;
}

export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  sources?: SourceReference[];
  responseTimeMs?: number;
}

export interface ChatRequest {
  question: string;
  conversation_id?: string | null;
}

export interface ChatResponse {
  answer: string;
  sources: SourceReference[];
  conversation_id: string;
  response_time_ms: number;
}

export interface Conversation {
  id: string;
  title: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface ConversationMessageResponse {
  id: string;
  conversation_id: string;
  role: MessageRole | "system";
  content: string;
  sources?: SourceReference[];
  created_at?: string | null;
}
