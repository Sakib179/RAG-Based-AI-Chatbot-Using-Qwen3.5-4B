"use client";

import { LogOut, Plus, X } from "lucide-react";
import { useEffect, useRef, useState, type KeyboardEvent } from "react";

import { DocumentUpload } from "@/components/chat/DocumentUpload";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import type { Conversation } from "@/types/chat";

interface ChatSidebarProps {
  desktopOpen: boolean;
  mobileOpen: boolean;
  email?: string | null;
  busy: boolean;
  onCloseMobile: () => void;
  onNewConversation: () => void;
  onLogout: () => void;
  conversations: Conversation[];
  selectedConversationId: string | null;
  onSelectConversation: (conversation: Conversation) => void;
  externalFile?: File | null;
  onExternalFileHandled?: () => void;
}

export function ChatSidebar({ desktopOpen, mobileOpen, email, busy, conversations, selectedConversationId, onCloseMobile, onNewConversation, onSelectConversation, onLogout, externalFile, onExternalFileHandled }: ChatSidebarProps) {
  const [width, setWidth] = useState(288);
  const panelRef = useRef<HTMLElement>(null);
  const previousFocus = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!mobileOpen) return;
    previousFocus.current = document.activeElement as HTMLElement | null;
    panelRef.current?.querySelector<HTMLButtonElement>("button")?.focus();
    const onEscape = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") onCloseMobile();
    };
    window.addEventListener("keydown", onEscape);
    return () => {
      window.removeEventListener("keydown", onEscape);
      previousFocus.current?.focus();
    };
  }, [mobileOpen, onCloseMobile]);

  const clampWidth = (value: number) => Math.max(240, Math.min(value, 400, window.innerWidth / 2));
  const keepFocusInDrawer = (event: KeyboardEvent<HTMLElement>) => {
    if (!mobileOpen || window.matchMedia("(min-width: 768px)").matches || event.key !== "Tab") return;
    const controls = panelRef.current?.querySelectorAll<HTMLElement>("button:not(:disabled), a[href], [tabindex='0']");
    if (!controls?.length) return;
    const first = controls[0];
    const last = controls[controls.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault(); last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault(); first.focus();
    }
  };

  return (
    <>
      {mobileOpen && <button className="fixed inset-0 z-30 bg-slate-950/50 md:hidden" onClick={onCloseMobile} aria-label="Close sidebar" />}
      <aside
        id="chat-sidebar"
        ref={panelRef}
        aria-label="Knowledge workspace sidebar"
        onKeyDown={keepFocusInDrawer}
        style={{ width }}
        className={`${mobileOpen ? "flex" : "hidden"} ${desktopOpen ? "md:flex" : "md:hidden"} fixed inset-y-0 left-0 z-40 max-w-[85vw] shrink-0 flex-col border-r border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900 md:relative md:z-auto md:max-w-none`}
      >
        <div className="flex items-center gap-3 px-2 py-2">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-teal-600 text-white">✦</div>
          <span className="flex-1 font-bold">Knowledge Chat</span>
          <Button variant="ghost" className="p-2 md:hidden" onClick={onCloseMobile} aria-label="Close sidebar"><X size={18} /></Button>
        </div>
        <Button onClick={onNewConversation} disabled={busy} className="mt-8 w-full justify-start gap-2"><Plus size={17} />New conversation</Button>
        <div className="min-h-0 flex-1 overflow-y-auto">
          <DocumentUpload externalFile={externalFile} onExternalFileHandled={onExternalFileHandled} />
          <p className="mt-8 px-2 text-xs font-semibold uppercase tracking-wider text-slate-400">Recent conversations</p>
          {conversations.length === 0 ? (
            <p className="px-2 pt-4 text-sm text-slate-400">No saved conversations yet.</p>
          ) : (
            <div className="mt-3 space-y-1">
              {conversations.map((conversation) => (
                <button
                  type="button"
                  key={conversation.id}
                  disabled={busy}
                  onClick={() => onSelectConversation(conversation)}
                  title={conversation.title || "Untitled conversation"}
                  aria-current={selectedConversationId === conversation.id ? "true" : undefined}
                  className={`w-full truncate rounded-xl px-2 py-2 text-left text-sm disabled:cursor-wait disabled:opacity-60 ${selectedConversationId === conversation.id ? "bg-teal-50 font-semibold text-teal-700 dark:bg-teal-950/50 dark:text-teal-300" : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"}`}
                >
                  {conversation.title || "Untitled conversation"}
                </button>
              ))}
            </div>
          )}
        </div>
        <div className="mt-4 border-t border-slate-200 pt-4 dark:border-slate-800">
          <div className="flex items-center gap-3 px-2"><Avatar name={email} /><span className="min-w-0 flex-1 truncate text-sm">{email}</span><Button variant="ghost" onClick={onLogout} className="p-2" aria-label="Log out"><LogOut size={17} /></Button></div>
        </div>
        <div
          role="separator"
          tabIndex={0}
          aria-label="Resize sidebar"
          aria-orientation="vertical"
          aria-valuemin={240}
          aria-valuemax={400}
          aria-valuenow={width}
          className="absolute inset-y-0 -right-1 hidden w-2 cursor-col-resize touch-none hover:bg-teal-500/30 focus-visible:bg-teal-500/30 focus-visible:outline-none md:block"
          onPointerDown={(event) => { event.preventDefault(); event.currentTarget.setPointerCapture(event.pointerId); }}
          onPointerMove={(event) => {
            if (event.currentTarget.hasPointerCapture(event.pointerId)) {
              setWidth(clampWidth(event.clientX - (panelRef.current?.getBoundingClientRect().left ?? 0)));
            }
          }}
          onPointerUp={(event) => { if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId); }}
          onKeyDown={(event) => {
            if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
              event.preventDefault();
              setWidth((current) => clampWidth(current + (event.key === "ArrowRight" ? 16 : -16)));
            }
          }}
        />
      </aside>
    </>
  );
}
