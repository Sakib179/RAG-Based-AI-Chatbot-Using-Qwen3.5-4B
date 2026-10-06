import { api } from "@/services/api";
import type { ChatRequest, ChatResponse, Conversation, ConversationMessageResponse } from "@/types/chat";

export async function sendMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>("/api/chat", request);
  return response.data;
}

export async function listConversations(): Promise<Conversation[]> {
  const response = await api.get<Conversation[]>("/api/chat/conversations");
  return response.data;
}

export async function loadConversation(conversationId: string): Promise<ConversationMessageResponse[]> {
  const response = await api.get<ConversationMessageResponse[]>(
    `/api/chat/conversations/${encodeURIComponent(conversationId)}`,
  );
  return response.data;
}
