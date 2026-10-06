import { Bot, UserRound } from "lucide-react";

import { Avatar } from "@/components/ui/avatar";
import type { ChatMessage } from "@/types/chat";
import { SourceReference } from "@/components/chat/SourceReference";
import { MarkdownContent } from "@/components/chat/MarkdownContent";
import { mergeSourceReferences } from "@/utils/sources";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const sources = !isUser && message.sources ? mergeSourceReferences(message.sources) : [];
  return <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
    {isUser ? <Avatar name="You" /> : <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-teal-600 text-white"><Bot size={18} /></div>}
    <div className={`max-w-[85%] space-y-2 sm:max-w-[75%] ${isUser ? "items-end text-right" : ""}`}>
      <div className={`rounded-2xl px-4 py-3 text-sm leading-6 ${isUser ? "rounded-br-md bg-teal-600 text-white" : "rounded-bl-md bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-100"}`}>
        {isUser ? <p className="whitespace-pre-wrap">{message.content}</p> : <MarkdownContent content={message.content} />}
      </div>
      {!isUser && sources.length > 0 && <div className="flex flex-wrap gap-2"><span className="sr-only">Sources:</span>{sources.map((source, index) => <SourceReference key={`${source.file}-${index}`} source={source} />)}</div>}
      {!isUser && message.responseTimeMs !== undefined && <p className="text-xs text-slate-400">Answered in {(message.responseTimeMs / 1000).toFixed(1)}s</p>}
    </div>
    {isUser && <UserRound className="sr-only" />}
  </div>;
}
