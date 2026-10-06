import { Bot, UserRound } from "lucide-react";

import { Avatar } from "@/components/ui/avatar";
import type { ChatMessage } from "@/types/chat";
import { SourceReference } from "@/components/chat/SourceReference";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
    {isUser ? <Avatar name="You" /> : <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-teal-600 text-white"><Bot size={18} /></div>}
    <div className={`max-w-[85%] space-y-2 sm:max-w-[75%] ${isUser ? "items-end text-right" : ""}`}>
      <div className={`rounded-2xl px-4 py-3 text-sm leading-6 ${isUser ? "rounded-br-md bg-teal-600 text-white" : "rounded-bl-md bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-100"}`}>
        <p className="whitespace-pre-wrap">{message.content}</p>
      </div>
      {!isUser && message.sources && message.sources.length > 0 && <div className="flex flex-wrap gap-2"><span className="sr-only">Sources:</span>{message.sources.map((source, index) => <SourceReference key={`${source.file}-${source.page ?? index}`} source={source} />)}</div>}
    </div>
    {isUser && <UserRound className="sr-only" />}
  </div>;
}
