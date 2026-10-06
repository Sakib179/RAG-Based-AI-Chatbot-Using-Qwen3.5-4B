"use client";

import Link from "next/link";
import { Moon, PanelLeft, Sun } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useRef, useState } from "react";

import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { ChatInput } from "@/components/chat/ChatInput";
import { ChatSidebar } from "@/components/chat/ChatSidebar";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { useTheme } from "@/providers/ThemeProvider";
import { SessionError } from "@/services/api";
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
  const [needsLogin, setNeedsLogin] = useState(false);
  const [desktopSidebarOpen, setDesktopSidebarOpen] = useState(true);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const sending = useRef(false);
  const closeMobileSidebar = useCallback(() => setMobileSidebarOpen(false), []);

  const newConversation = () => {
    if (sending.current) return;
    setMessages([]); setConversationId(null); setError(""); setNeedsLogin(false);
    closeMobileSidebar();
  };
  const askQuestion = async (question: string) => {
    if (sending.current) return;
    sending.current = true;
    setError(""); setNeedsLogin(false); setIsLoading(true);
    const userMessage: ChatMessage = { id: crypto.randomUUID(), role: "user", content: question };
    setMessages((current) => [...current, userMessage]);
    try {
      const response = await sendMessage({ question, conversation_id: conversationId });
      setConversationId(response.conversation_id);
      setMessages((current) => [...current, { id: crypto.randomUUID(), role: "assistant", content: response.answer, sources: response.sources }]);
    } catch (reason) {
      setError(getErrorMessage(reason));
      setNeedsLogin(reason instanceof SessionError);
    } finally {
      sending.current = false;
      setIsLoading(false);
    }
  };
  const handleLogout = async () => {
    try { await logout(); router.replace("/login"); }
    catch (reason) { setError(getErrorMessage(reason)); }
  };

  return (
    <div className="flex h-dvh overflow-hidden bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <ChatSidebar desktopOpen={desktopSidebarOpen} mobileOpen={mobileSidebarOpen} email={user?.email} busy={isLoading} onCloseMobile={closeMobileSidebar} onNewConversation={newConversation} onLogout={handleLogout} />
      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 shrink-0 items-center justify-between gap-2 border-b border-slate-200 bg-white/80 px-4 backdrop-blur dark:border-slate-800 dark:bg-slate-900/80 sm:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <Button variant="ghost" className="p-2 md:hidden" aria-label="Open sidebar and uploads" aria-expanded={mobileSidebarOpen} aria-controls="chat-sidebar" onClick={() => setMobileSidebarOpen(true)}><PanelLeft size={19} /></Button>
            <Button variant="ghost" className="hidden p-2 md:inline-flex" aria-label={desktopSidebarOpen ? "Collapse sidebar" : "Expand sidebar"} aria-expanded={desktopSidebarOpen} aria-controls="chat-sidebar" onClick={() => setDesktopSidebarOpen((open) => !open)}><PanelLeft size={19} /></Button>
            <p className="truncate text-sm font-semibold md:hidden">Knowledge Chat</p>
            <p className="hidden text-sm text-slate-500 dark:text-slate-400 md:block">Grounded answers from your documents</p>
          </div>
          <Button variant="ghost" className="p-2" onClick={toggleTheme} aria-label={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}>{theme === "light" ? <Moon size={18} /> : <Sun size={18} />}</Button>
        </header>
        <ChatWindow messages={messages} isLoading={isLoading} />
        <div className="shrink-0 px-4 pb-4 sm:px-8">
          <div className="mx-auto max-w-3xl">
            <ChatInput disabled={isLoading} onSubmit={askQuestion} />
            {error && <div role="alert" className="mt-2 rounded-xl bg-rose-50 px-3 py-2 text-center text-sm text-rose-700 dark:bg-rose-950/30 dark:text-rose-300">{error}{needsLogin && <Link href="/login" className="ml-2 font-semibold underline">Sign in</Link>}</div>}
            <p className="mt-2 text-center text-xs text-slate-400">Answers are generated from indexed knowledge-base documents.</p>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function ChatPage() {
  return <ProtectedRoute><ChatPageContent /></ProtectedRoute>;
}
