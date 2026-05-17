"use client";

import { useState } from "react";
import clsx from "clsx";

const DISCIPLINES = [
  { code: "biology", label: "Biology" },
  { code: "medicine", label: "Medicine" },
  { code: "chemistry", label: "Chemistry" },
  { code: "physics", label: "Physics" },
  { code: "computer-science", label: "Computer Science" },
  { code: "psychology", label: "Psychology" },
  { code: "economics", label: "Economics" },
  { code: "sociology", label: "Sociology" },
];

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "zh", label: "Chinese" },
  { code: "ja", label: "Japanese" },
  { code: "es", label: "Spanish" },
  { code: "de", label: "German" },
];

const EXAMPLE_QUERIES = [
  { text: "CRISPR gene therapy for sickle cell disease (2020–2026)", yearFrom: 2020, yearTo: 2026 },
  { text: "LLM-based code generation safety in production systems (2021–2026)", yearFrom: 2021, yearTo: 2026 },
  { text: "AI-assisted drug discovery for rare diseases (2019–2026)", yearFrom: 2019, yearTo: 2026 },
  { text: "Quantum error correction in fault-tolerant quantum computers (2018–2026)", yearFrom: 2018, yearTo: 2026 },
];

const MAX_PAPERS_PRESETS = [10, 20, 30, 50, 100];

interface QuerySectionProps {
  onRun: (payload: {
    query: string;
    years: [number, number] | null;
    max_papers: number;
    disciplines: string[];
    output_language: string;
  }) => Promise<void>;
  loading: boolean;
}

export function QuerySection({ onRun, loading }: QuerySectionProps) {
  const [query, setQuery] = useState("");
  const [yearFrom, setYearFrom] = useState<string>("2018");
  const [yearTo, setYearTo] = useState<string>("2026");
  const [disciplines, setDisciplines] = useState<string[]>([]);
  const [outputLanguage, setOutputLanguage] = useState("en");
  const [maxPapers, setMaxPapers] = useState(30);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [yearError, setYearError] = useState<string | null>(null);

  const toggleDiscipline = (code: string) => {
    setDisciplines((prev) =>
      prev.includes(code) ? prev.filter((x) => x !== code) : [...prev, code]
    );
  };

  const validateYears = (): boolean => {
    if (!yearFrom || !yearTo) {
      setYearError(null);
      return true;
    }
    const from = +yearFrom;
    const to = +yearTo;
    if (from > to) {
      setYearError("Start year must be ≤ end year");
      return false;
    }
    setYearError(null);
    return true;
  };

  const handleRun = () => {
    if (!validateYears()) return;
    const years: [number, number] | null =
      yearFrom && yearTo ? [+yearFrom, +yearTo] : null;
    onRun({
      query,
      years,
      max_papers: maxPapers,
      disciplines,
      output_language: outputLanguage,
    });
  };

  const handleReset = () => {
    setQuery("");
    setYearFrom("2018");
    setYearTo("2026");
    setOutputLanguage("en");
    setMaxPapers(30);
    setDisciplines([]);
    setYearError(null);
  };

  const handleExampleClick = (example: (typeof EXAMPLE_QUERIES)[0]) => {
    setQuery(example.text);
    setYearFrom(String(example.yearFrom));
    setYearTo(String(example.yearTo));
    setYearError(null);
  };

  const inputBase =
    "w-full rounded-lg border bg-[#1F2933] border-[rgba(148,163,184,0.35)] " +
    "px-3 py-2 text-sm text-[#E5E7EB] placeholder:text-[#9CA3AF] " +
    "focus:outline-none focus:ring-2 focus:ring-[#3B82F6]/60 focus:border-transparent " +
    "transition-colors duration-150";

  const labelStyle =
    "block text-[11px] font-semibold text-[#9CA3AF] tracking-[0.08em] uppercase mb-1.5";

  const isRunDisabled = loading || !query.trim() || yearError !== null;

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
          placeholder="e.g. CRISPR gene therapy clinical trials 2020–2026"
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey) && !isRunDisabled) {
              handleRun();
            }
          }}
        />
      </div>

      {/* Example Queries */}
      <div>
        <span className={labelStyle}>Example Queries</span>
        <div className="flex flex-wrap gap-2 mt-1">
          {EXAMPLE_QUERIES.map((example, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleExampleClick(example)}
              className={clsx(
                "px-3 py-1.5 rounded-lg text-[12px] font-medium border transition-all duration-150",
                "bg-[#1F2933] border-[rgba(148,163,184,0.25)] text-[#9CA3AF]",
                "hover:border-[#3B82F6] hover:text-[#3B82F6] hover:bg-[rgba(59,130,246,0.08)]",
                "focus:outline-none focus:ring-2 focus:ring-[#3B82F6]/60",
                "active:scale-[0.98]"
              )}
              aria-label={`Use example query: ${example.text}`}
            >
              {example.text}
            </button>
          ))}
        </div>
      </div>

      {/* Row 2: Controls + CTA */}
      <div className="flex flex-wrap items-end gap-4 justify-between">
        <div className="flex flex-wrap items-end gap-3">
          {/* Year range */}
          <div>
            <label className={labelStyle}>Year Range</label>
            <div className="flex items-center gap-1.5">
              <input
                type="number"
                className={clsx(
                  inputBase + " w-[70px] text-center",
                  yearError && "border-[#F43F5E] focus:ring-[#F43F5E]/60"
                )}
                placeholder="From"
                min={1900}
                max={2100}
                value={yearFrom}
                onChange={(e) => { setYearFrom(e.target.value); setYearError(null); }}
                onBlur={validateYears}
                aria-label="Start year"
              />
              <span className="text-[#9CA3AF] text-sm">—</span>
              <input
                type="number"
                className={clsx(
                  inputBase + " w-[70px] text-center",
                  yearError && "border-[#F43F5E] focus:ring-[#F43F5E]/60"
                )}
                placeholder="To"
                min={1900}
                max={2100}
                value={yearTo}
                onChange={(e) => { setYearTo(e.target.value); setYearError(null); }}
                onBlur={validateYears}
                aria-label="End year"
              />
            </div>
            {yearError && (
              <p className="text-[10px] text-[#F43F5E] mt-1" role="alert">{yearError}</p>
            )}
          </div>

          {/* Max papers */}
          <div>
            <label htmlFor="max-papers" className={labelStyle}>Max Papers</label>
            <div className="flex items-center gap-1.5">
              <input
                id="max-papers"
                type="number"
                className={inputBase + " w-[72px] text-center"}
                min={5}
                max={100}
                value={maxPapers}
                onChange={(e) => {
                  const val = +e.target.value;
                  if (val >= 5 && val <= 100) setMaxPapers(val);
                }}
                aria-label="Maximum number of papers"
              />
              <div className="flex gap-0.5">
                {MAX_PAPERS_PRESETS.map((preset) => (
                  <button
                    key={preset}
                    type="button"
                    onClick={() => setMaxPapers(preset)}
                    className={clsx(
                      "px-1.5 py-0.5 rounded text-[10px] font-medium transition-all duration-100",
                      maxPapers === preset
                        ? "bg-[#3B82F6] text-white"
                        : "bg-[#1F2933] text-[#9CA3AF] hover:bg-[rgba(59,130,246,0.15)] hover:text-[#3B82F6]"
                    )}
                    aria-label={`Set max papers to ${preset}`}
                  >
                    {preset}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Advanced toggle */}
          <button
            onClick={() => setShowAdvanced((v) => !v)}
            className="text-[11px] text-[#9CA3AF] hover:text-[#3B82F6] transition-colors underline underline-offset-2"
          >
            {showAdvanced ? "Fewer options" : "More options"}
          </button>
        </div>

        {/* Right: Reset + Run CTA */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleReset}
            disabled={loading}
            className={clsx(
              "inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium",
              "text-[#9CA3AF] border border-[rgba(148,163,184,0.35)] transition-all duration-150",
              "disabled:opacity-40 disabled:cursor-not-allowed",
              !loading && "hover:border-[rgba(148,163,184,0.55)] hover:text-[#E5E7EB]"
            )}
            aria-label="Reset all fields to defaults"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" />
              <path d="M21 3v5h-5" />
              <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" />
              <path d="M3 21v-5h5" />
            </svg>
            Reset
          </button>

          <button
            onClick={handleRun}
            disabled={isRunDisabled}
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
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
              <path d="M3 2.5L11 7L3 11.5V2.5Z" fill="currentColor" />
            </svg>
            {loading ? "Analyzing…" : "Run analysis"}
          </button>
        </div>
      </div>

      {/* Advanced: Disciplines + Output Language */}
      {showAdvanced && (
        <div className="flex flex-wrap gap-4 pt-1 border-t border-[rgba(148,163,184,0.15)]">
          {/* Disciplines chip select */}
          <div className="flex-1 min-w-0">
            <span className={labelStyle}>Disciplines</span>
            <div className="flex flex-wrap gap-1.5 mt-1">
              {DISCIPLINES.map((d) => {
                const active = disciplines.includes(d.code);
                return (
                  <button
                    key={d.code}
                    type="button"
                    onClick={() => toggleDiscipline(d.code)}
                    className={clsx(
                      "px-2.5 py-1 rounded-full text-[12px] font-medium border transition-all duration-100",
                      active
                        ? "bg-[rgba(59,130,246,0.2)] border-[#3B82F6] text-[#3B82F6]"
                        : "bg-[#1F2933] border-[rgba(148,163,184,0.25)] text-[#9CA3AF] hover:border-[rgba(148,163,184,0.5)] hover:text-[#E5E7EB]"
                    )}
                    aria-pressed={active}
                    aria-label={`Toggle ${d.label} discipline`}
                  >
                    {d.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Output language */}
          <div>
            <label htmlFor="out-lang" className={labelStyle}>Output Language</label>
            <select
              id="out-lang"
              className={inputBase + " w-[120px] cursor-pointer"}
              value={outputLanguage}
              onChange={(e) => setOutputLanguage(e.target.value)}
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>{l.label}</option>
              ))}
            </select>
          </div>
        </div>
      )}
    </section>
  );
}