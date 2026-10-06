"use client";

import { useEffect, useRef } from "react";

import { ScrollArea } from "@/components/ui/scroll-area";
import type { ChatMessage } from "@/types/chat";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { TypingIndicator } from "@/components/chat/TypingIndicator";

interface ChatWindowProps { messages: ChatMessage[]; isLoading?: boolean; }

export function ChatWindow({ messages, isLoading = false }: ChatWindowProps) {
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, isLoading]);

  return <ScrollArea className="flex-1 px-4 py-6 sm:px-8"><div className="mx-auto flex w-full max-w-3xl flex-col gap-6">
    {messages.length === 0 && <div className="flex min-h-[45vh] flex-col items-center justify-center text-center"><div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-teal-100 text-2xl dark:bg-teal-950">✦</div><h2 className="text-xl font-semibold text-slate-900 dark:text-white">Ask your knowledge base</h2><p className="mt-2 max-w-md text-sm text-slate-500">Answers are grounded in the documents you provide.</p></div>}
    {messages.map((message) => <MessageBubble key={message.id} message={message} />)}
    {isLoading && <div className="flex gap-3"><div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-teal-600 text-white">✦</div><TypingIndicator /></div>}
    <div ref={endRef} />
  </div></ScrollArea>;
}
