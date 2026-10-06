"use client";

import Link from "next/link";
import { Moon, PanelLeft, Sun } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState, type DragEvent } from "react";

import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { ChatInput } from "@/components/chat/ChatInput";
import { ChatSidebar } from "@/components/chat/ChatSidebar";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { isSupportedDocument } from "@/components/chat/DocumentUpload";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { useTheme } from "@/providers/ThemeProvider";
import { SessionError } from "@/services/api";
import { listConversations, loadConversation, sendMessage } from "@/services/chat";
import type { ChatMessage, Conversation } from "@/types/chat";
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
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [droppedFile, setDroppedFile] = useState<File | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [desktopSidebarOpen, setDesktopSidebarOpen] = useState(true);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const sending = useRef(false);
  const closeMobileSidebar = useCallback(() => setMobileSidebarOpen(false), []);

  const refreshConversations = useCallback(async () => {
    try { setConversations(await listConversations()); }
    catch (reason) { setError(getErrorMessage(reason)); }
  }, []);

  useEffect(() => {
    if (!user) return;
    const timer = window.setTimeout(() => { void refreshConversations(); }, 0);
    return () => window.clearTimeout(timer);
  }, [refreshConversations, user]);

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
      setMessages((current) => [...current, { id: crypto.randomUUID(), role: "assistant", content: response.answer, sources: response.sources, responseTimeMs: response.response_time_ms }]);
      void refreshConversations();
    } catch (reason) {
      setError(getErrorMessage(reason));
      setNeedsLogin(reason instanceof SessionError);
    } finally {
      sending.current = false;
      setIsLoading(false);
    }
  };
  const selectConversation = async (conversation: Conversation) => {
    if (sending.current) return;
    sending.current = true;
    setError(""); setNeedsLogin(false); setIsLoading(true);
    try {
      const persisted = await loadConversation(conversation.id);
      setConversationId(conversation.id);
      setMessages(persisted.filter((message) => message.role !== "system").map((message) => ({ id: message.id, role: message.role as "user" | "assistant", content: message.content, sources: message.sources })));
      closeMobileSidebar();
    } catch (reason) { setError(getErrorMessage(reason)); }
    finally { sending.current = false; setIsLoading(false); }
  };
  const handleLogout = async () => {
    try { await logout(); router.replace("/login"); }
    catch (reason) { setError(getErrorMessage(reason)); }
  };

  const handleDrop = (event: DragEvent<HTMLElement>) => {
    event.preventDefault();
    setIsDragActive(false);
    const file = event.dataTransfer.files[0];
    if (!file) return;
    if (!isSupportedDocument(file)) {
      setError("Drop a PDF, TXT, DOCX, HTML, PNG, JPG, or JPEG file.");
      return;
    }
    setError("");
    setDroppedFile(file);
  };

  return (
    <div className="flex h-dvh overflow-hidden bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <ChatSidebar desktopOpen={desktopSidebarOpen} mobileOpen={mobileSidebarOpen} email={user?.email} busy={isLoading} conversations={conversations} selectedConversationId={conversationId} onCloseMobile={closeMobileSidebar} onNewConversation={newConversation} onSelectConversation={selectConversation} onLogout={handleLogout} externalFile={droppedFile} onExternalFileHandled={() => setDroppedFile(null)} />
      <main className="relative flex min-w-0 flex-1 flex-col" onDragEnter={(event) => { event.preventDefault(); setIsDragActive(true); }} onDragOver={(event) => event.preventDefault()} onDragLeave={(event) => { if (event.currentTarget === event.target) setIsDragActive(false); }} onDrop={handleDrop}>
        {isDragActive && <div className="pointer-events-none absolute inset-3 z-20 flex items-center justify-center rounded-2xl border-2 border-dashed border-teal-500 bg-teal-50/90 text-sm font-semibold text-teal-800 dark:bg-teal-950/90 dark:text-teal-200">Drop a document to add it to the knowledge base</div>}
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
            <p className="mt-2 text-center text-xs text-slate-400">Answers use indexed knowledge-base documents. Drop a PDF, DOCX, TXT, HTML, or image into the chat to upload it.</p>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function ChatPage() {
  return <ProtectedRoute><ChatPageContent /></ProtectedRoute>;
}
