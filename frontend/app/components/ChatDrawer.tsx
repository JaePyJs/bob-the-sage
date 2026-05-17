"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import clsx from "clsx";

interface Message {
  id: number;
  role: "user" | "sage";
  text: string;
}

const SYSTEM_PROMPT = `You are SAGE, a research assistant powered by IBM Bob. You help users understand and explore their research session findings. Be concise and cite specific details from the analysis.`;

export function ChatDrawer() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 0,
      role: "sage",
      text: "Hello. I can help you explore this session's findings. Ask me anything about the review, citation network, or proposal.",
    },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    if (!input.trim() || sending) return;
    const text = input.trim();
    setInput("");
    setSending(true);

    const userMsg: Message = { id: Date.now(), role: "user", text };
    setMessages((prev) => [...prev, userMsg]);

    // Echo back a placeholder response for now (Bob will wire real LLM)
    await new Promise((r) => setTimeout(r, 900));
    const sageMsg: Message = {
      id: Date.now() + 1,
      role: "sage",
      text: `[Placeholder] You asked: "${text}". This chat will be connected to IBM Bob's multi-model inference in a later skill.`,
    };
    setMessages((prev) => [...prev, sageMsg]);
    setSending(false);
  };

  return (
    <>
      {/* Toggle button */}
      <button
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? "Close chat" : "Open chat"}
        className={clsx(
          "fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-full",
          "pl-4 pr-5 py-3 text-sm font-semibold shadow-lg transition-all duration-200",
          "border",
          open
            ? "bg-[#111827] border-[rgba(148,163,184,0.35)] text-[#E5E7EB]"
            : "bg-[#3B82F6] border-[#3B82F6] text-white hover:bg-[#2563EB]"
        )}
      >
        {/* Chat icon */}
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
        <span className="hidden sm:block">Chat</span>
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={clsx("transition-transform duration-200", open && "rotate-180")}
          aria-hidden="true"
        >
          <polyline points="18 15 12 9 6 15" />
        </svg>
      </button>

      {/* Drawer panel */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="fixed bottom-20 right-6 z-50 w-[360px] max-w-[calc(100vw-48px)] rounded-xl overflow-hidden border shadow-2xl"
            style={{
              backgroundColor: "#111827",
              borderColor: "rgba(148,163,184,0.35)",
            }}
          >
            {/* Header */}
            <div
              className="flex items-center justify-between px-4 py-3 border-b"
              style={{ borderColor: "rgba(148,163,184,0.15)" }}
            >
              <div className="flex items-center gap-2">
                <div
                  className="w-2 h-2 rounded-full bg-[#3B82F6]"
                  aria-hidden="true"
                />
                <span className="text-sm font-semibold text-[#E5E7EB]">SAGE</span>
                <span className="text-[11px] text-[#9CA3AF] font-mono">Gemini 2.0</span>
              </div>
              <button
                onClick={() => setOpen(false)}
                className="text-[#9CA3AF] hover:text-[#E5E7EB] transition-colors"
                aria-label="Close chat"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>

            {/* Messages */}
            <div
              className="flex flex-col gap-3 p-4 overflow-y-auto"
              style={{ maxHeight: "340px" }}
            >
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={clsx(
                    "flex flex-col gap-0.5",
                    msg.role === "user" ? "items-end" : "items-start"
                  )}
                >
                  {msg.role === "sage" && (
                    <span className="text-[10px] font-semibold text-[#3B82F6] tracking-wider uppercase ml-1">
                      SAGE
                    </span>
                  )}
                  <div
                    className={clsx(
                      "px-3 py-2 rounded-xl text-sm leading-relaxed max-w-[85%]",
                      msg.role === "user"
                        ? "bg-[#3B82F6]/20 border border-[#3B82F6]/30 text-[#E5E7EB] rounded-tr-none"
                        : "bg-[#1F2933] text-[#E5E7EB] rounded-tl-none"
                    )}
                  >
                    {msg.text}
                  </div>
                </div>
              ))}
              {sending && (
                <div className="flex items-center gap-2 text-[#9CA3AF] text-sm">
                  <div className="flex gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#9CA3AF] animate-bounce" style={{ animationDelay: "0ms" }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-[#9CA3AF] animate-bounce" style={{ animationDelay: "150ms" }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-[#9CA3AF] animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                  <span className="text-[12px]">SAGE is thinking…</span>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* Input bar */}
            <div
              className="flex items-center gap-2 p-3 border-t"
              style={{ borderColor: "rgba(148,163,184,0.15)" }}
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && send()}
                placeholder="Ask about this session…"
                className={clsx(
                  "flex-1 rounded-lg px-3 py-2 text-sm",
                  "bg-[#1F2933] border border-[rgba(148,163,184,0.25)]",
                  "text-[#E5E7EB] placeholder:text-[#9CA3AF]",
                  "focus:outline-none focus:ring-1 focus:ring-[#3B82F6]/60 focus:border-transparent",
                  "transition-colors duration-150"
                )}
              />
              <button
                onClick={send}
                disabled={!input.trim() || sending}
                className={clsx(
                  "p-2 rounded-lg transition-all duration-150",
                  "disabled:opacity-40 disabled:cursor-not-allowed",
                  "bg-[#3B82F6] text-white hover:bg-[#2563EB] active:scale-95"
                )}
                aria-label="Send message"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}