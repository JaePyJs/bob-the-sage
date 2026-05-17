"use client";

import React, { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import clsx from "clsx";

// ─── Types ────────────────────────────────────────────────────
type PipelineStage = "pending" | "discovery" | "extraction" | "synthesis" | "complete" | "error";

type StageId = "discovery" | "extraction" | "synthesis" | "graph" | "proposal";

interface StageMeta {
  id: StageId;
  title: string;
  subtitle: string;
}

const STAGES: StageMeta[] = [
  { id: "discovery",   title: "Discovery",   subtitle: "Fetching sources"      },
  { id: "extraction", title: "Extraction",   subtitle: "Parsing evidence"     },
  { id: "synthesis",  title: "Synthesis",   subtitle: "Writing review"      },
  { id: "graph",       title: "Graph",        subtitle: "Building network"     },
  { id: "proposal",    title: "Proposal",     subtitle: "Generating draft"    },
];

const STAGE_MAP: Record<string, StageId> = {
  discovery: "discovery",
  extraction: "extraction",
  synthesis: "synthesis",
  complete: "proposal",
};

// ─── Icons (inline SVG, no emoji) ─────────────────────────────
function IconDiscovery() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.35-4.35" />
    </svg>
  );
}

function IconExtraction() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 2L2 7l10 5 10-5-10-5z" />
      <path d="M2 17l10 5 10-5" />
      <path d="M2 12l10 5 10-5" />
    </svg>
  );
}

function IconSynthesis() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
    </svg>
  );
}

function IconGraph() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="5" r="2" />
      <circle cx="5" cy="19" r="2" />
      <circle cx="19" cy="19" r="2" />
      <path d="M12 7v4M8.5 16.5 10 11M15.5 16.5 14 11" />
    </svg>
  );
}

function IconProposal() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10 9 9 9 8 9" />
    </svg>
  );
}

function IconCheck() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

const STAGE_ICONS: Record<StageId, () => React.JSX.Element> = {
  discovery:  IconDiscovery,
  extraction: IconExtraction,
  synthesis:  IconSynthesis,
  graph:      IconGraph,
  proposal:   IconProposal,
};

// ─── Progress bar ─────────────────────────────────────────────
function ProgressBar({ progress }: { progress: number }) {
  return (
    <div
      className="w-full h-1.5 rounded-full overflow-hidden"
      style={{ backgroundColor: "#1F2933" }}
      role="progressbar"
      aria-valuenow={progress}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div
        className="h-full rounded-full transition-all duration-700 ease-out"
        style={{
          width: `${progress}%`,
          backgroundColor: "#3B82F6",
          boxShadow: progress > 0 ? "0 0 8px rgba(59,130,246,0.6)" : "none",
        }}
      />
    </div>
  );
}

// ─── Stage Node ───────────────────────────────────────────────
type StageStatus = "idle" | "active" | "complete";

function getStageStatus(
  stageId: StageId,
  activeStage: StageId | null,
  completedStages: Set<StageId>,
): StageStatus {
  if (completedStages.has(stageId)) return "complete";
  if (stageId === activeStage) return "active";
  return "idle";
}

function StageNode({
  meta,
  status,
  index,
}: {
  meta: StageMeta;
  status: StageStatus;
  index: number;
}) {
  const Icon = STAGE_ICONS[meta.id];

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.3, ease: "easeOut" }}
      className={clsx(
        "flex flex-col items-center gap-1.5 rounded-lg border p-3 text-center",
        "min-w-0 transition-all duration-200",
        status === "complete" && "bg-[rgba(59,130,246,0.15)] border-[#3B82F6]/50",
        status === "active" && "bg-[#111827] border-[#3B82F6]/70 shadow-[0_0_0_1px_rgba(59,130,246,0.5),0_0_12px_rgba(59,130,246,0.2)]",
        status === "idle" && "bg-[#111827] border-[rgba(148,163,184,0.15)]",
      )}
    >
      <motion.div
        className={clsx(
          "w-9 h-9 rounded-full flex items-center justify-center border transition-all duration-300",
          status === "complete" && "bg-[#3B82F6] border-[#3B82F6] text-white",
          status === "active" && "border-[#3B82F6] text-[#3B82F6] shadow-[0_0_0_1px_rgba(59,130,246,0.5)]",
          status === "idle" && "border-[rgba(148,163,184,0.25)] text-[#9CA3AF]",
        )}
        animate={status === "active" ? { scale: [1, 1.06, 1] } : { scale: 1 }}
        transition={{ duration: 1.4, repeat: Infinity, ease: "easeInOut" }}
      >
        {status === "complete" ? <IconCheck /> : <Icon />}
      </motion.div>
      <span
        className={clsx(
          "text-[11px] font-semibold leading-tight",
          status === "complete" && "text-[#3B82F6]",
          status === "active" && "text-[#E5E7EB]",
          status === "idle" && "text-[#9CA3AF]",
        )}
      >
        {meta.title}
      </span>
      <span className="text-[10px] text-[#9CA3AF] leading-tight hidden sm:block">
        {meta.subtitle}
      </span>
    </motion.div>
  );
}

// ─── Main Component ───────────────────────────────────────────
interface RealtimePipelineProps {
  sessionId: string | null;
  query?: string | null;
  onComplete?: (results: unknown) => void;
}

export function RealtimePipeline({ sessionId, query, onComplete }: RealtimePipelineProps) {
  const [activeStageId, setActiveStageId] = useState<StageId | null>(null);
  const [completedStages, setCompletedStages] = useState<Set<StageId>>(new Set());
  const [progress, setProgress] = useState(0);
  const [papersFound, setPapersFound] = useState<number | null>(null);
  const [papersAnalyzed, setPapersAnalyzed] = useState<number | null>(null);
  const [themesIdentified, setThemesIdentified] = useState<number | null>(null);
  const [polling, setPolling] = useState(false);

  // Poll for pipeline status
  const pollStatus = useCallback(async () => {
    if (!sessionId) return;

    try {
      const res = await fetch(`/api/pipeline-status?session_id=${sessionId}`);
      if (!res.ok) return;
      const data = await res.json();

      const displayStage = STAGE_MAP[data.stage] || null;

      if (displayStage) {
        if (activeStageId && displayStage !== activeStageId) {
          setCompletedStages((prev) => new Set([...prev, activeStageId!]));
        }
        if (displayStage !== activeStageId) {
          setActiveStageId(displayStage);
        }
      }

      setProgress(data.progress || 0);
      if (data.papers_found) setPapersFound(data.papers_found);
      if (data.papers_analyzed) setPapersAnalyzed(data.papers_analyzed);
      if (data.themes_identified) setThemesIdentified(data.themes_identified);

      if (data.stage === "complete") {
        setCompletedStages(new Set(STAGES.map((s) => s.id)));
        setActiveStageId(null);
        setPolling(false);
        if (data.results && onComplete) {
          onComplete(data.results);
        }
      } else if (data.stage === "error") {
        setPolling(false);
      }

      return data.stage;
    } catch (err) {
      console.error("Poll error:", err);
      return null;
    }
  }, [sessionId, activeStageId, onComplete]);

  useEffect(() => {
    if (!sessionId) {
      setActiveStageId(null);
      setCompletedStages(new Set());
      setProgress(0);
      setPapersFound(null);
      setPapersAnalyzed(null);
      setThemesIdentified(null);
      setPolling(false);
      return;
    }

    setPolling(true);

    // Poll every 2 seconds
    const interval = setInterval(async () => {
      const stage = await pollStatus();
      if (stage === "complete" || stage === "error") {
        clearInterval(interval);
      }
    }, 2000);

    // Initial poll
    pollStatus();

    return () => clearInterval(interval);
  }, [sessionId, pollStatus]);

  return (
    <section
      className="bg-[#111827] border border-[rgba(148,163,184,0.35)] rounded-xl p-4"
      aria-label="Research pipeline status"
    >
      {/* Header row */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="text-[11px] font-semibold text-[#9CA3AF] tracking-[0.08em] uppercase">
            Pipeline
          </span>
          {sessionId && (
            <span className="font-mono text-[11px] text-[#9CA3AF]/70">
              session {sessionId.slice(0, 8)}
            </span>
          )}
          {sessionId && (
            <span
              className={clsx(
                "w-1.5 h-1.5 rounded-full transition-colors duration-300",
                polling ? "bg-[#3B82F6] animate-pulse" : progress === 100 ? "bg-[#22C55E]" : "bg-[#9CA3AF]",
              )}
              title={polling ? "Processing" : progress === 100 ? "Complete" : "Waiting"}
            />
          )}
        </div>

        {/* Live stats */}
        {sessionId && (
          <div className="flex gap-4 text-[11px] text-[#9CA3AF]">
            <AnimatePresence mode="wait">
              {papersFound !== null && (
                <motion.span
                  key={`pf-${papersFound}`}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="font-mono tabular-nums"
                >
                  papers&nbsp;
                  <span className="text-[#E5E7EB]">{papersFound}</span>
                </motion.span>
              )}
            </AnimatePresence>
            <AnimatePresence mode="wait">
              {papersAnalyzed !== null && (
                <motion.span
                  key={`pa-${papersAnalyzed}`}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="font-mono tabular-nums"
                >
                  analyzed&nbsp;
                  <span className="text-[#E5E7EB]">{papersAnalyzed}</span>
                </motion.span>
              )}
            </AnimatePresence>
            <AnimatePresence mode="wait">
              {themesIdentified !== null && (
                <motion.span
                  key={`ti-${themesIdentified}`}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="font-mono tabular-nums"
                >
                  themes&nbsp;
                  <span className="text-[#E5E7EB]">{themesIdentified}</span>
                </motion.span>
              )}
            </AnimatePresence>
          </div>
        )}
      </div>

      {/* Progress bar */}
      {sessionId ? (
        <ProgressBar progress={progress} />
      ) : (
        <div className="w-full h-1.5 rounded-full" style={{ backgroundColor: "#1F2933" }} />
      )}

      {/* Stage nodes */}
      <div className="grid grid-cols-5 gap-2 mt-3">
        {STAGES.map((s, i) => (
          <StageNode
            key={s.id}
            meta={s}
            index={i}
            status={getStageStatus(s.id, activeStageId, completedStages)}
          />
        ))}
      </div>

      {/* Idle state */}
      {!sessionId && (
        <p className="text-[12px] text-[#9CA3AF] text-center mt-3">
          Enter a query above to start the pipeline
        </p>
      )}
    </section>
  );
}