"use client";

import { useState, useCallback } from "react";
import Image from "next/image";
import { QuerySection }     from "./components/QuerySection";
import { RealtimePipeline } from "./components/RealtimePipeline";
import { ResultsTabs }      from "./components/ResultsTabs";
import { ChatDrawer }       from "./components/ChatDrawer";

export default function Page() {
  const [session,   setSession]   = useState<string | null>(null);
  const [loading,   setLoading]   = useState(false);
  const [error,     setError]     = useState<string | null>(null);
  const [completed, setCompleted] = useState(false);
  const [results,   setResults]   = useState<unknown>(null);
  const [query,         setQuery]         = useState<string>("");
  const [outputLanguage, setOutputLanguage] = useState<string>("en");

  const handleRun = useCallback(
    async (payload: {
      query: string;
      years: [number, number] | null;
      max_papers: number;
      disciplines: string[];
      output_language: string;
    }) => {
      setLoading(true);
      setSession(null);
      setError(null);
      setCompleted(false);
      setResults(null);
      setQuery(payload.query);
      setOutputLanguage(payload.output_language ?? "en");

      try {
        const body: Record<string, unknown> = {
          query:           payload.query,
          max_papers:      payload.max_papers,
          output_language: payload.output_language,
        };
        if (payload.years) body.years = payload.years;
        if (payload.disciplines.length) body.disciplines = payload.disciplines;

        const res  = await fetch("/api/sage", {
          method:  "POST",
          headers: { "Content-Type": "application/json" },
          body:    JSON.stringify(body),
        });
        const data = await res.json();

        if (res.ok && data.session_id) {
          setSession(data.session_id);
        } else {
          setError(data.detail ?? "Request failed");
        }
      } catch (err) {
        setError(String(err));
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return (
    <main
      className="mx-auto w-full max-w-5xl px-6 py-6 flex flex-col gap-6 min-h-screen"
      style={{ backgroundColor: "#0B1018" }}
    >
      {/* ── Header ─────────────────────────────────── */}
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg overflow-hidden flex items-center justify-center">
            <Image
              src="/Logo.png"
              alt="SAGE Logo"
              width={32}
              height={32}
              className="object-contain"
              priority
            />
          </div>
          <div>
            <h1 className="text-[22px] font-semibold text-[#E5E7EB] leading-none">
              SAGE
            </h1>
            <p className="text-[11px] text-[#9CA3AF] tracking-wide">
              Systematic Academic Guidance Engine
            </p>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex items-center gap-5">
          <a href="#" className="text-[13px] text-[#9CA3AF] hover:text-[#E5E7EB] transition-colors">About</a>
          <a href="#" className="text-[13px] text-[#9CA3AF] hover:text-[#E5E7EB] transition-colors">Docs</a>
          <div className="w-px h-4 bg-[rgba(148,163,184,0.3)]" aria-hidden="true" />
          <span
            className="text-[11px] px-2 py-0.5 rounded font-mono"
            style={{ backgroundColor: "rgba(59,130,246,0.12)", color: "#3B82F6" }}
          >
            Gemini powered
          </span>
        </nav>
      </header>

      {/* ── Query Section ───────────────────────────── */}
      <QuerySection onRun={handleRun} loading={loading} />

      {/* ── Error banner ───────────────────────────── */}
      {error && (
        <div
          className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm"
          style={{ backgroundColor: "rgba(244,63,94,0.1)", border: "1px solid rgba(244,63,94,0.3)", color: "#F43F5E" }}
          role="alert"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          {error}
        </div>
      )}

      {/* ── Pipeline ────────────────────────────────── */}
      <RealtimePipeline
        sessionId={session}
        query={query}
        onComplete={(r) => { setCompleted(true); setResults(r); }}
      />

      {/* ── Results ────────────────────────────────── */}
      <ResultsTabs completed={completed} results={results} query={query} outputLanguage={outputLanguage} />

      {/* ── Chat Drawer ─────────────────────────────── */}
      <ChatDrawer results={results} />
    </main>
  );
}