export function TypingIndicator() {
  return <div className="flex items-center gap-1 rounded-2xl rounded-bl-md bg-slate-100 px-4 py-3 dark:bg-slate-800" aria-label="Assistant is typing"><span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]" /><span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]" /><span className="h-2 w-2 animate-bounce rounded-full bg-slate-400" /></div>;
}
