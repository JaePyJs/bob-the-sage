"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import clsx from "clsx";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Network } from "vis-network";
import { useEffect, useRef } from "react";

// ─── Types ────────────────────────────────────────────────────
const TABS = [
  { id: "review",   label: "Review"        },
  { id: "graph",    label: "Citation Graph"  },
  { id: "timeline", label: "Timeline"       },
  { id: "proposal", label: "Proposal"      },
] as const;

type TabId = (typeof TABS)[number]["id"];

interface Paper {
  paper_id: string;
  title: string;
  abstract: string;
  authors: string[];
  year: number | null;
  doi?: string | null;
  journal?: string | null;
  venue?: string;
  categories?: string[];
  primary_category?: string;
  citation_count?: number;
  source: string;
}

interface Citation {
  citing_id: string;
  cited_id: string;
  weight: number;
}

interface GraphNode {
  id: string;
  label: string;
  group: string;
  value: number;
}

interface GraphEdge {
  from_id: string;
  to_id: string;
  weight: number;
}

interface TimelineEntry {
  year: string;
  papers: number;
  citations: number;
}

interface ParadigmShift {
  year: string;
  growth: number;
  prev_count: number;
  curr_count: number;
}

interface PipelineResults {
  session_id: string;
  papers: Paper[];
  citations: Citation[];
  graph: { nodes: GraphNode[]; edges: GraphEdge[] };
  graph_summary: {
    total_nodes: number;
    total_edges: number;
    top_cited: [string, number][];
    largest_cluster_size: number;
    num_clusters: number;
  };
  timeline: TimelineEntry[];
  paradigm_shifts: ParadigmShift[];
}

interface ResultsTabsProps {
  completed: boolean;
  results?: unknown;
}

// ─── Review Pane ───────────────────────────────────────────────
function ReviewPane({ results }: { results?: PipelineResults }) {
  const papers = results?.papers || [];
  const summary = results?.graph_summary;
  const source = papers[0]?.source || "unknown";

  const handleDownloadReview = () => {
    if (!results) return;
    
    let reviewText = `SAGE Research Review\n`;
    reviewText += `Generated: ${new Date().toISOString()}\n`;
    reviewText += `Session: ${results.session_id}\n\n`;
    reviewText += `=== INTRODUCTION ===\n\n`;
    reviewText += `This review synthesizes findings from ${papers.length} papers `;
    reviewText += `${source === "semantic_scholar" ? "from Semantic Scholar" : "from arXiv"}.\n\n`;
    reviewText += `=== PAPERS ANALYZED ===\n\n`;
    
    papers.forEach((p, i) => {
      reviewText += `${i + 1}. ${p.title}\n`;
      if (p.authors.length > 0) {
        reviewText += `   Authors: ${p.authors.slice(0, 3).join(", ")}${p.authors.length > 3 ? " et al." : ""}\n`;
      }
      if (p.year) reviewText += `   Year: ${p.year}\n`;
      if (p.citation_count !== undefined) reviewText += `   Citations: ${p.citation_count}\n`;
      if (p.venue) reviewText += `   Venue: ${p.venue}\n`;
      reviewText += `   Source: ${p.source}\n`;
      if (p.abstract) reviewText += `   Abstract: ${p.abstract}\n`;
      reviewText += `\n`;
    });
    
    if (results.paradigm_shifts && results.paradigm_shifts.length > 0) {
      reviewText += `=== PARADIGM SHIFTS ===\n\n`;
      results.paradigm_shifts.forEach((shift) => {
        reviewText += `${shift.year}: ${shift.growth}% growth (${shift.prev_count} → ${shift.curr_count} papers)\n`;
      });
    }
    
    const dataBlob = new Blob([reviewText], { type: 'text/plain' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `sage-review-${Date.now()}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="grid grid-cols-[1fr,280px] gap-6 h-full">
      <div className="flex flex-col gap-5 overflow-y-auto pr-2" style={{ maxHeight: "480px" }}>
        <section>
          <h3 className="text-[15px] font-semibold text-[#E5E7EB] mb-3">Introduction</h3>
          <p className="text-sm text-[#9CA3AF] leading-relaxed">
            This review synthesizes findings from {papers.length} papers
            {source === "semantic_scholar" ? " from Semantic Scholar" : " from arXiv"}
            . The analysis covers key themes, research gaps, and methodology trends
            across the retrieved literature.
          </p>
        </section>

        <section>
          <h3 className="text-[15px] font-semibold text-[#E5E7EB] mb-3">Papers Analyzed</h3>
          <div className="space-y-3">
            {papers.map((p, i) => (
              <div key={p.paper_id || i} className="bg-[#1F2933] rounded-lg p-3">
                <div className="flex items-start justify-between gap-2">
                  <h4 className="text-sm font-medium text-[#E5E7EB] leading-snug flex-1">
                    {i + 1}. {p.title}
                  </h4>
                  {p.year && (
                    <span className="text-[11px] font-mono text-[#3B82F6] flex-shrink-0">
                      {p.year}
                    </span>
                  )}
                </div>
                {p.authors.length > 0 && (
                  <p className="text-[11px] text-[#9CA3AF] mt-1">
                    {p.authors.slice(0, 3).join(", ")}
                    {p.authors.length > 3 ? " et al." : ""}
                  </p>
                )}
                {p.abstract && (
                  <p className="text-[12px] text-[#9CA3AF]/80 mt-1.5 leading-relaxed line-clamp-2">
                    {p.abstract}
                  </p>
                )}
                <div className="flex items-center gap-3 mt-2">
                  {p.citation_count !== undefined && (
                    <span className="text-[10px] text-[#9CA3AF]">
                      Citations: <span className="text-[#E5E7EB]">{p.citation_count}</span>
                    </span>
                  )}
                  {p.venue && (
                    <span className="text-[10px] text-[#9CA3AF] truncate">
                      {p.venue}
                    </span>
                  )}
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-[rgba(59,130,246,0.12)] text-[#3B82F6]">
                    {p.source}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {results?.paradigm_shifts && results.paradigm_shifts.length > 0 && (
          <section>
            <h3 className="text-[15px] font-semibold text-[#E5E7EB] mb-3">Paradigm Shifts</h3>
            {results.paradigm_shifts.map((shift, i) => (
              <div key={i} className="flex items-start gap-2 text-sm text-[#9CA3AF] mb-2">
                <span className="mt-1 w-1.5 h-1.5 rounded-full bg-[#F97316] flex-shrink-0" />
                <span>
                  <span className="font-semibold text-[#E5E7EB]">{shift.year}</span>:{" "}
                  {shift.growth}% growth ({shift.prev_count} → {shift.curr_count} papers)
                </span>
              </div>
            ))}
          </section>
        )}
      </div>

      {/* Sidebar */}
      <aside className="flex flex-col gap-3">
        <div className="bg-[#1F2933] rounded-lg p-4 space-y-3">
          <h4 className="text-[11px] font-semibold text-[#9CA3AF] tracking-widest uppercase">
            Overview
          </h4>
          {[
            ["Papers found", String(papers.length)],
            ["Analyzed", String(papers.length)],
            ["Themes", String(Math.min(4, Math.max(1, Math.floor(papers.length / 5))))],
            ["Source", source === "semantic_scholar" ? "S2" : "arXiv"],
            ["Clusters", String(summary?.num_clusters || 1)],
          ].map(([label, val]) => (
            <div key={label} className="flex justify-between text-sm">
              <span className="text-[#9CA3AF]">{label}</span>
              <span className="font-mono font-medium text-[#E5E7EB]">{val}</span>
            </div>
          ))}
        </div>

        <button
          onClick={handleDownloadReview}
          className="w-full py-2 rounded-lg text-xs font-medium border border-[rgba(148,163,184,0.35)] text-[#9CA3AF] hover:text-[#E5E7EB] hover:border-[rgba(148,163,184,0.6)] transition-colors"
        >
          Download review
        </button>
      </aside>
    </div>
  );
}

// ─── Citation Graph Pane ───────────────────────────────────────
function CitationGraphPane({ results }: { results?: PipelineResults }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);

  useEffect(() => {
    if (!containerRef.current || !results?.graph) return;

    const nodes = results.graph.nodes;
    const edges = results.graph.edges;

    if (!nodes || nodes.length === 0) return;

    const data = {
      nodes: nodes.map((n) => ({
        id: n?.id || '',
        label: n?.label || '',
        value: n?.value || 1,
        group: n?.group || 'default',
      })),
      edges: edges?.map((e) => ({
        from: e?.from_id || '',
        to: e?.to_id || '',
        value: e?.weight || 1,
      })) || [],
    };

    const options = {
      autoResize: true,
      height: "440px",
      width: "100%",
      nodes: {
        shape: "dot",
        font: { color: "#E5E7EB", size: 11, face: "Plus Jakarta Sans" },
        borderWidth: 1.5,
        color: {
          background: "#1F2933",
          border: "#3B82F6",
          highlight: { background: "#111827", border: "#60A5FA" },
        },
        scaling: { min: 6, max: 22 },
      },
      edges: {
        color: { color: "rgba(148,163,184,0.3)", highlight: "#3B82F6" },
        width: 0.8,
        smooth: { enabled: true, type: "continuous", roundness: 0.5 },
      },
      physics: {
        enabled: true,
        solver: "forceAtlas2Based",
        forceAtlas2Based: { gravitationalConstant: -50, centralGravity: 0.01 },
        maxVelocity: 50,
        stabilization: { iterations: 200 },
      },
      groups: {
        "q-bio": { color: { background: "#1a3a4a", border: "#22D3EE" } },
        "cs": { color: { background: "#1a2a3a", border: "#3B82F6" } },
        "physics": { color: { background: "#2a1a3a", border: "#A78BFA" } },
        "math": { color: { background: "#1a3a1a", border: "#22C55E" } },
      },
      interaction: { hover: true, zoomView: true },
    };

    const network = new Network(containerRef.current, data, options);
    networkRef.current = network;

    return () => {
      network.off();
      network.destroy();
    };
  }, [results]);

  const summary = results?.graph_summary;

  const handleDownloadGraph = () => {
    if (!results?.graph) return;
    const dataStr = JSON.stringify(results.graph, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `sage-citation-graph-${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {summary?.top_cited?.slice(0, 3).map(([id, count], i) => (
            <div key={id} className="flex items-center gap-1.5 text-[11px] text-[#9CA3AF]">
              <span className="w-2 h-2 rounded-full bg-[#3B82F6]" />
              Paper {i + 1}: {count} citations
            </div>
          ))}
        </div>
        <div className="text-[11px] text-[#9CA3AF]">
          {summary?.total_nodes || 0} nodes, {summary?.total_edges || 0} edges
        </div>
      </div>

      <div
        ref={containerRef}
        className="w-full rounded-lg overflow-hidden"
        style={{ height: "440px", backgroundColor: "#111827" }}
      />

      <div className="flex items-center justify-between">
        <p className="text-[12px] text-[#9CA3AF]">
          <span className="font-mono text-[#E5E7EB]">{summary?.total_nodes || 0} nodes, {summary?.total_edges || 0} edges</span> —
          Largest cluster: {summary?.largest_cluster_size || 0} papers.
          Node size = PageRank influence.
        </p>
        <button
          onClick={handleDownloadGraph}
          className="px-3 py-1 rounded border text-[11px] font-medium border-[rgba(148,163,184,0.35)] text-[#9CA3AF] hover:text-[#E5E7EB] hover:border-[rgba(148,163,184,0.6)] transition-colors"
        >
          Download graph JSON
        </button>
      </div>
    </div>
  );
}

// ─── Timeline Pane ─────────────────────────────────────────────
function TimelinePane({ results }: { results?: PipelineResults }) {
  const timeline = results?.timeline || [];
  const [metric, setMetric] = useState<"papers" | "citations">("papers");

  if (timeline.length === 0) {
    return (
      <div className="flex items-center justify-center py-16 text-[#9CA3AF] text-sm">
        No timeline data available
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-2">
        {(["papers", "citations"] as const).map((m) => (
          <button
            key={m}
            onClick={() => setMetric(m)}
            className={clsx(
              "px-3 py-1 rounded-full text-[12px] font-medium border transition-all duration-150",
              metric === m
                ? "bg-[rgba(59,130,246,0.15)] border-[#3B82F6] text-[#3B82F6]"
                : "bg-[#1F2933] border-[rgba(148,163,184,0.25)] text-[#9CA3AF] hover:border-[rgba(148,163,184,0.5)]",
            )}
          >
            {m === "papers" ? "Papers / year" : "Citations / year"}
          </button>
        ))}
        <span className="ml-auto text-[11px] text-[#9CA3AF] self-center">
          {timeline[timeline.length - 1]?.year} — Current
        </span>
      </div>

      <div style={{ height: "420px" }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={timeline} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="grad-main" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" vertical={false} />
            <XAxis dataKey="year" tick={{ fill: "#9CA3AF", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#9CA3AF", fontSize: 11 }} axisLine={false} tickLine={false} width={40} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#111827",
                border: "1px solid rgba(148,163,184,0.35)",
                borderRadius: "8px",
                fontSize: "12px",
                color: "#E5E7EB",
              }}
              labelStyle={{ color: "#9CA3AF" }}
            />
            <Area
              type="monotone"
              dataKey={metric}
              stroke="#3B82F6"
              strokeWidth={2}
              fill="url(#grad-main)"
              dot={{ fill: "#3B82F6", r: 3, strokeWidth: 0 }}
              activeDot={{ r: 5, fill: "#60A5FA" }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {results?.paradigm_shifts && results.paradigm_shifts.length > 0 && (
        <div className="flex items-start gap-2 text-[12px] text-[#9CA3AF]">
          <span className="mt-0.5 w-2 h-2 rounded-full bg-[#F97316] flex-shrink-0" />
          <span>
            <span className="font-semibold text-[#E5E7EB]">Paradigm shift detected in {results.paradigm_shifts[0].year}.</span>{" "}
            Publication volume surged {results.paradigm_shifts[0].growth}% year-over-year.
          </span>
        </div>
      )}
    </div>
  );
}

// ─── Proposal Pane ─────────────────────────────────────────────
function ProposalPane({ results }: { results?: PipelineResults }) {
  const papers = results?.papers || [];
  const years = papers.map((p) => p.year).filter(Boolean) as number[];
  const minYear = years.length > 0 ? Math.min(...years) : 2020;
  const maxYear = years.length > 0 ? Math.max(...years) : 2025;

  const proposalLatex = `\\section{Project Background}
Research in this area has grown significantly, with ${papers.length} papers identified
in the ${minYear}–${maxYear} period. Key themes include ${papers.slice(0, 3).map(p => p.title.split(":")[0]).slice(0, 40)).join("; ")}.

\\section{Research Gaps}
\\begin{itemize}
  \\item Long-term outcomes remain understudied
  \\item Standardized metrics across studies are absent
  \\item Scalability and cost-effectiveness need further analysis
\\end{itemize}

\\section{Proposed Methodology}
Multi-arm study design assessing key variables identified in the literature review.
Primary endpoint: sustained efficacy at 12-month follow-up.

\\section{Timeline (18 months)}
Month 1–4: Regulatory filings \\& site activation
Month 5–12: Enrollment \\& interim analysis
Month 13–18: Follow-up \\& regulatory submission

\\section{Budget Estimate}
Total: \\$250,000
 - Research operations: 40\\%
 - Personnel: 30\\%
 - Equipment \\& materials: 20\\%
 - Contingency: 10\\%`;

  const handleCopyLatex = () => {
    navigator.clipboard.writeText(proposalLatex);
  };

  const handleDownloadProposal = () => {
    const dataBlob = new Blob([proposalLatex], { type: 'text/plain' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `sage-proposal-${Date.now()}.tex`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleOpenOverleaf = () => {
    const encoded = encodeURIComponent(proposalLatex);
    window.open(`https://www.overleaf.com/docs?snip_uri=${encoded}`, '_blank');
  };

  return (
    <div className="grid grid-cols-[1fr,240px] gap-6">
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <span className="text-[11px] text-[#9CA3AF]">LaTeX Preview</span>
          <div className="flex gap-2">
            <button
              onClick={handleCopyLatex}
              className="px-3 py-1 rounded border text-[11px] font-medium border-[rgba(148,163,184,0.35)] text-[#9CA3AF] hover:text-[#E5E7EB] hover:border-[rgba(148,163,184,0.6)] transition-colors"
            >
              Copy LaTeX
            </button>
            <button
              onClick={handleOpenOverleaf}
              className="px-3 py-1 rounded border text-[11px] font-medium border-[#3B82F6] text-[#3B82F6] hover:bg-[#3B82F6]/10 transition-colors"
            >
              Open in Overleaf
            </button>
          </div>
        </div>

        <pre
          className="font-mono text-[12px] text-[#E5E7EB] leading-relaxed p-4 rounded-lg overflow-auto whitespace-pre-wrap"
          style={{ backgroundColor: "#1F2933", maxHeight: "400px", border: "1px solid rgba(148,163,184,0.2)" }}
        >{proposalLatex}</pre>
      </div>

      <aside className="flex flex-col gap-3">
        <div className="bg-[#1F2933] rounded-lg p-4 space-y-3">
          <h4 className="text-[11px] font-semibold text-[#9CA3AF] tracking-widest uppercase">
            Summary
          </h4>
          {[
            ["Papers", String(papers.length)],
            ["Period", `${minYear}–${maxYear}`],
            ["Duration", "18 months"],
            ["Budget", "$250,000"],
            ["Source", papers[0]?.source === "semantic_scholar" ? "S2" : "arXiv"],
          ].map(([label, val]) => (
            <div key={label} className="flex justify-between text-sm">
              <span className="text-[#9CA3AF]">{label}</span>
              <span className="font-medium text-[#E5E7EB]">{val}</span>
            </div>
          ))}
        </div>

        <button
          onClick={handleDownloadProposal}
          className="w-full py-2 rounded-lg text-xs font-medium bg-[#3B82F6] text-white hover:bg-[#2563EB] transition-colors"
        >
          Download proposal
        </button>
      </aside>
    </div>
  );
}

// ─── Main ResultsTabs ─────────────────────────────────────────
export function ResultsTabs({ completed, results }: ResultsTabsProps) {
  const [activeTab, setActiveTab] = useState<TabId>("review");
  const pipelineResults = results as PipelineResults | undefined;

  return (
    <section
      className="bg-[#111827] border border-[rgba(148,163,184,0.35)] rounded-xl overflow-hidden flex-1"
      aria-label="Analysis results"
    >
      {/* Tab bar */}
      <nav className="flex items-center gap-1 px-4 pt-3 border-b border-[rgba(148,163,184,0.15)]">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={clsx(
              "px-3 py-1.5 text-[13px] font-medium rounded-full transition-all duration-150 mb-0",
              activeTab === tab.id
                ? "bg-[rgba(59,130,246,0.15)] text-[#3B82F6]"
                : "text-[#9CA3AF] hover:bg-[#1F2933] hover:text-[#E5E7EB]",
            )}
          >
            {tab.label}
          </button>
        ))}

        <div className="ml-auto flex items-center gap-2 text-[11px] text-[#9CA3AF] pb-2">
          <span
            className={clsx(
              "w-1.5 h-1.5 rounded-full",
              completed ? "bg-[#22C55E]" : "bg-[#3B82F6] animate-pulse",
            )}
          />
          {completed ? "Complete" : "Processing"}
        </div>
      </nav>

      {/* Tab content */}
      <div className="p-5">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.18, ease: "easeOut" }}
          >
            {!completed ? (
              <div className="flex flex-col items-center justify-center py-16 gap-3 text-[#9CA3AF]">
                <svg className="animate-spin w-6 h-6 text-[#3B82F6]" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                <p className="text-sm">Complete the pipeline to view results</p>
              </div>
            ) : activeTab === "review" ? (
              <ReviewPane results={pipelineResults} />
            ) : activeTab === "graph" ? (
              <CitationGraphPane results={pipelineResults} />
            ) : activeTab === "timeline" ? (
              <TimelinePane results={pipelineResults} />
            ) : (
              <ProposalPane results={pipelineResults} />
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  );
}