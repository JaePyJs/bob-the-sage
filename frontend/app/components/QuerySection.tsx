"use client";

import { useState } from "react";
import clsx from "clsx";

const DISCIPLINES = [
  "Biology",
  "Medicine",
  "Chemistry",
  "Physics",
  "Computer Science",
  "Psychology",
  "Economics",
  "Sociology",
];

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "de", label: "German" },
  { code: "fr", label: "French" },
  { code: "es", label: "Spanish" },
  { code: "zh", label: "Chinese" },
  { code: "ja", label: "Japanese" },
  { code: "ko", label: "Korean" },
];

interface QuerySectionProps {
  onRun: (payload: {
    query: string;
    language: string;
    years: [number, number] | null;
    max_papers: number;
    disciplines: string[];
    output_language: string;
  }) => Promise<void>;
  loading: boolean;
}

export function QuerySection({ onRun, loading }: QuerySectionProps) {
  const [query, setQuery] = useState("");
  const [yearFrom, setYearFrom] = useState<string>("");
  const [yearTo, setYearTo] = useState<string>("");
  const [disciplines, setDisciplines] = useState<string[]>([]);
  const [language, setLanguage] = useState("en");
  const [outputLanguage, setOutputLanguage] = useState("en");
  const [maxPapers, setMaxPapers] = useState(50);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const toggleDiscipline = (d: string) => {
    setDisciplines((prev) =>
      prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d]
    );
  };

  const handleRun = () => {
    const years: [number, number] | null =
      yearFrom && yearTo ? [+yearFrom, +yearTo] : null;

    onRun({
      query,
      language,
      years,
      max_papers: maxPapers,
      disciplines,
      output_language: outputLanguage,
    });
  };

  const inputBase =
    "w-full rounded-lg border bg-[#1F2933] border-[rgba(148,163,184,0.35)] " +
    "px-3 py-2 text-sm text-[#E5E7EB] placeholder:text-[#9CA3AF] " +
    "focus:outline-none focus:ring-2 focus:ring-[#3B82F6]/60 focus:border-transparent " +
    "transition-colors duration-150";

  const labelStyle =
    "block text-[11px] font-semibold text-[#9CA3AF] tracking-[0.08em] uppercase mb-1.5";

  return (
    <section
      className="bg-[#111827] border border-[rgba(148,163,184,0.35)] rounded-xl p-5 flex flex-col gap-4"
      aria-label="Research query input"
    >
      {/* Row 1: Query textarea */}
      <div>
        <label htmlFor="query-input" className={labelStyle}>
          Research Query
        </label>
        <textarea
          id="query-input"
          className={inputBase + " resize-none min-h-[72px]"}
          rows={3}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. CRISPR gene therapy clinical trials 2020–2025"
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleRun();
          }}
        />
      </div>

      {/* Row 2: Controls + CTA */}
      <div className="flex flex-wrap items-end gap-4 justify-between">
        {/* Left: compact controls */}
        <div className="flex flex-wrap items-end gap-3">
          {/* Year range */}
          <div>
            <label className={labelStyle}>Year Range</label>
            <div className="flex items-center gap-1.5">
              <input
                type="number"
                className={inputBase + " w-[70px] text-center"}
                placeholder="From"
                min={1900}
                max={2030}
                value={yearFrom}
                onChange={(e) => setYearFrom(e.target.value)}
              />
              <span className="text-[#9CA3AF] text-sm">—</span>
              <input
                type="number"
                className={inputBase + " w-[70px] text-center"}
                placeholder="To"
                min={1900}
                max={2030}
                value={yearTo}
                onChange={(e) => setYearTo(e.target.value)}
              />
            </div>
          </div>

          {/* Language */}
          <div>
            <label htmlFor="lang-select" className={labelStyle}>
              Language
            </label>
            <select
              id="lang-select"
              className={inputBase + " w-[120px] cursor-pointer"}
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.label}
                </option>
              ))}
            </select>
          </div>

          {/* Max papers */}
          <div>
            <label htmlFor="max-papers" className={labelStyle}>
              Max Papers
            </label>
            <input
              id="max-papers"
              type="number"
              className={inputBase + " w-[72px] text-center"}
              min={1}
              max={500}
              value={maxPapers}
              onChange={(e) => setMaxPapers(+e.target.value)}
            />
          </div>

          {/* Advanced toggle */}
          <button
            onClick={() => setShowAdvanced((v) => !v)}
            className="text-[11px] text-[#9CA3AF] hover:text-[#3B82F6] transition-colors underline underline-offset-2"
          >
            {showAdvanced ? "Fewer options" : "More options"}
          </button>
        </div>

        {/* Right: Run CTA */}
        <button
          onClick={handleRun}
          disabled={loading || !query.trim()}
          className={clsx(
            "inline-flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold",
            "text-white transition-all duration-150",
            "disabled:opacity-40 disabled:cursor-not-allowed",
            loading
              ? "bg-[#3B82F6]/70 cursor-not-allowed"
              : "bg-[#3B82F6] hover:bg-[#2563EB] active:scale-[0.97]"
          )}
          aria-label="Run research analysis"
        >
          {/* Play icon */}
          <svg
            width="14"
            height="14"
            viewBox="0 0 14 14"
            fill="none"
            aria-hidden="true"
          >
            <path
              d="M3 2.5L11 7L3 11.5V2.5Z"
              fill="currentColor"
            />
          </svg>
          {loading ? "Analyzing…" : "Run analysis"}
        </button>
      </div>

      {/* Advanced: Disciplines + Output Language */}
      {showAdvanced && (
        <div className="flex flex-wrap gap-4 pt-1 border-t border-[rgba(148,163,184,0.15)]">
          {/* Disciplines chip select */}
          <div className="flex-1 min-w-0">
            <span className={labelStyle}>Disciplines</span>
            <div className="flex flex-wrap gap-1.5 mt-1">
              {DISCIPLINES.map((d) => {
                const active = disciplines.includes(d);
                return (
                  <button
                    key={d}
                    type="button"
                    onClick={() => toggleDiscipline(d)}
                    className={clsx(
                      "px-2.5 py-1 rounded-full text-[12px] font-medium border transition-all duration-100",
                      active
                        ? "bg-[rgba(59,130,246,0.2)] border-[#3B82F6] text-[#3B82F6]"
                        : "bg-[#1F2933] border-[rgba(148,163,184,0.25)] text-[#9CA3AF] hover:border-[rgba(148,163,184,0.5)] hover:text-[#E5E7EB]"
                    )}
                  >
                    {d}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Output language */}
          <div>
            <label htmlFor="out-lang" className={labelStyle}>
              Output Language
            </label>
            <select
              id="out-lang"
              className={inputBase + " w-[120px] cursor-pointer"}
              value={outputLanguage}
              onChange={(e) => setOutputLanguage(e.target.value)}
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}
    </section>
  );
}