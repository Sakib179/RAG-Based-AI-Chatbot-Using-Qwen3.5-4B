import { api } from "@/services/api";
import type { ChatRequest, ChatResponse } from "@/types/chat";

export async function sendMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>("/api/chat", request);
  return response.data;
}
