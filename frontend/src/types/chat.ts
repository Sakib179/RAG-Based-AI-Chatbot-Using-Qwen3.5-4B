export interface SourceReference {
  file: string;
  page?: number | null;
}

export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  sources?: SourceReference[];
}

export interface ChatRequest {
  question: string;
  conversation_id?: string | null;
}

export interface ChatResponse {
  answer: string;
  sources: SourceReference[];
  conversation_id: string;
}

export interface Conversation {
  id: string;
  title: string | null;
  created_at?: string;
  updated_at?: string;
}
