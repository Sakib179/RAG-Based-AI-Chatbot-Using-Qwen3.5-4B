"use client";

import { LogOut, Moon, Plus, Sun } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { ChatInput } from "@/components/chat/ChatInput";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";
import { useTheme } from "@/providers/ThemeProvider";
import { sendMessage } from "@/services/chat";
import type { ChatMessage } from "@/types/chat";
import { getErrorMessage } from "@/utils/errors";

function ChatPageContent() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const newConversation = () => { setMessages([]); setConversationId(null); setError(""); };
  const askQuestion = async (question: string) => {
    setError("");
    const userMessage: ChatMessage = { id: crypto.randomUUID(), role: "user", content: question };
    setMessages((current) => [...current, userMessage]);
    setIsLoading(true);
    try {
      const response = await sendMessage({ question, conversation_id: conversationId });
      setConversationId(response.conversation_id);
      setMessages((current) => [...current, { id: crypto.randomUUID(), role: "assistant", content: response.answer, sources: response.sources }]);
    } catch (reason) {
      setError(getErrorMessage(reason));
    } finally { setIsLoading(false); }
  };
  const handleLogout = async () => { await logout(); router.replace("/login"); };

  return <div className="flex min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
    <aside className="hidden w-72 shrink-0 flex-col border-r border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900 md:flex">
      <div className="flex items-center gap-3 px-2 py-2"><div className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal-600 text-white">✦</div><span className="font-bold">Knowledge Chat</span></div>
      <Button onClick={newConversation} className="mt-8 w-full justify-start gap-2"><Plus size={17} /> New conversation</Button>
      <div className="mt-8 flex-1"><p className="px-2 text-xs font-semibold uppercase tracking-wider text-slate-400">Recent conversations</p><p className="px-2 pt-4 text-sm text-slate-400">Conversation history will appear here.</p></div>
      <div className="border-t border-slate-200 pt-4 dark:border-slate-800"><div className="flex items-center gap-3 px-2"><Avatar name={user?.email} /><span className="min-w-0 flex-1 truncate text-sm">{user?.email}</span><button onClick={handleLogout} className="text-slate-400 hover:text-rose-600" aria-label="Log out"><LogOut size={17} /></button></div></div>
    </aside>
    <main className="flex min-h-screen min-w-0 flex-1 flex-col">
      <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white/80 px-4 backdrop-blur dark:border-slate-800 dark:bg-slate-900/80 sm:px-8"><div><p className="text-sm font-semibold md:hidden">Knowledge Chat</p><p className="hidden text-sm text-slate-500 md:block">Grounded answers from your documents</p></div><div className="flex items-center gap-2"><button onClick={toggleTheme} className="rounded-xl p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800" aria-label="Toggle theme">{theme === "light" ? <Moon size={18} /> : <Sun size={18} />}</button><button onClick={handleLogout} className="rounded-xl p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 md:hidden" aria-label="Log out"><LogOut size={18} /></button></div></header>
      <ChatWindow messages={messages} isLoading={isLoading} />
      <div className="px-4 pb-4 sm:px-8"><div className="mx-auto max-w-3xl"><Card className="border-0 bg-transparent shadow-none"><ChatInput disabled={isLoading} onSubmit={askQuestion} /></Card>{error && <div role="alert" className="mx-auto mt-2 max-w-3xl rounded-xl bg-rose-50 px-3 py-2 text-center text-sm text-rose-700 dark:bg-rose-950/30 dark:text-rose-300">{error}</div>}<p className="mt-2 text-center text-xs text-slate-400">Answers are generated from indexed knowledge-base documents.</p></div></div>
    </main>
  </div>;
}

export default function ChatPage() { return <ProtectedRoute><ChatPageContent /></ProtectedRoute>; }
