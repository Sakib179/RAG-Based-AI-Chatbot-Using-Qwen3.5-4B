"use client";

import { ArrowUp } from "lucide-react";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";

interface ChatInputProps { disabled?: boolean; onSubmit: (question: string) => void; }

export function ChatInput({ disabled = false, onSubmit }: ChatInputProps) {
  const [value, setValue] = useState("");
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const question = value.trim();
    if (!question || disabled) return;
    onSubmit(question);
    setValue("");
  };

  return <form onSubmit={handleSubmit} className="flex items-end gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm dark:border-slate-700 dark:bg-slate-900"><textarea value={value} onChange={(event) => setValue(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); event.currentTarget.form?.requestSubmit(); } }} placeholder="Ask about your knowledge base…" rows={1} maxLength={4000} disabled={disabled} className="max-h-32 min-h-11 flex-1 resize-none bg-transparent px-3 py-2.5 text-sm text-slate-900 outline-none placeholder:text-slate-400 dark:text-slate-100" aria-label="Question" /><Button type="submit" disabled={disabled || !value.trim()} className="h-11 w-11 rounded-xl p-0" aria-label="Send question"><ArrowUp size={18} /></Button></form>;
}
