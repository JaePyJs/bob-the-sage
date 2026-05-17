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
  query?: string;
  outputLanguage?: string;
}

interface SynthesisTheme { name: string; description: string; paper_indices: number[]; }
interface SynthesisGap { gap: string; evidence: string; impact: string; }
interface SynthesisResult {
  executive_summary: string;
  key_themes: SynthesisTheme[];
  research_gaps: SynthesisGap[];
  methodology_landscape: string;
  novel_questions: string[];
  consensus_findings: string;
  contradictions: string | null;
  ai_generated: boolean;
}

// ─── Review Pane ───────────────────────────────────────────────
function ReviewPane({ results, query, outputLanguage }: {
  results?: PipelineResults; query?: string; outputLanguage?: string;
}) {
  const papers = results?.papers || [];
  const summary = results?.graph_summary;
  const source = papers[0]?.source || "unknown";
  const [synthesis, setSynthesis] = useState<SynthesisResult | null>(null);
  const [synthesizing, setSynthesizing] = useState(false);
  const [synthError, setSynthError] = useState<string | null>(null);
  const [expandedPaper, setExpandedPaper] = useState<string | null>(null);

  // Auto-run when results arrive
  useEffect(() => {
    if (papers.length > 0 && !synthesis && !synthesizing) runSynthesis();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [results?.session_id]);

  const runSynthesis = async () => {
    if (!results || synthesizing) return;
    setSynthesizing(true);
    setSynthError(null);
    try {
      const res = await fetch("/api/synthesize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query || results.session_id,
          papers: results.papers,
          output_language: outputLanguage || "en",
        }),
      });
      const data = await res.json();
      if (data.executive_summary) setSynthesis(data);
      else setSynthError("AI synthesis unavailable.");
    } catch (_) {
      setSynthError("Synthesis failed — showing paper list.");
    } finally {
      setSynthesizing(false);
    }
  };

  const handleDownloadReview = () => {
    if (!results) return;
    const ts = new Date().toISOString().split("T")[0];
    let md = `# SAGE Research Review\n\n**Query:** ${query || results.session_id}\n**Generated:** ${new Date().toLocaleString()}\n\n---\n\n`;
    if (synthesis) {
      md += `## Executive Summary\n\n${synthesis.executive_summary}\n\n`;
      md += `## Key Themes\n\n` + synthesis.key_themes.map((t, i) => `### ${i + 1}. ${t.name}\n\n${t.description}`).join("\n\n") + "\n\n";
      md += `## Research Gaps\n\n` + synthesis.research_gaps.map((g, i) => `### Gap ${i + 1}: ${g.gap}\n\n**Evidence:** ${g.evidence}\n\n**Impact:** ${g.impact}`).join("\n\n") + "\n\n";
      if (synthesis.methodology_landscape) md += `## Methodology\n\n${synthesis.methodology_landscape}\n\n`;
      if (synthesis.novel_questions.length) md += `## Open Questions\n\n${synthesis.novel_questions.map((q, i) => `${i + 1}. ${q}`).join("\n")}\n\n`;
      md += `---\n\n`;
    }
    md += `## Papers (${papers.length})\n\n` + papers.map((p, i) => {
      let s = `### ${i + 1}. ${p.title}\n\n`;
      s += `**Authors:** ${p.authors.slice(0, 5).join(", ")}${p.authors.length > 5 ? " et al." : ""}  \n`;
      s += `**Year:** ${p.year} | **Citations:** ${p.citation_count ?? "?"} | **Source:** ${p.source}\n\n`;
      if (p.abstract) s += p.abstract + "\n\n";
      return s + "---\n\n";
    }).join("");
    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `sage-review-${ts}.md`;
    document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(url);
  };

  return (
    <div className="grid grid-cols-[1fr,280px] gap-6 h-full">
      <div className="flex flex-col gap-5 overflow-y-auto pr-2" style={{ maxHeight: "520px" }}>

        {/* Gemini spinning state */}
        {synthesizing && (
          <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-[rgba(59,130,246,0.08)] border border-[rgba(59,130,246,0.2)]">
            <svg className="animate-spin w-4 h-4 text-[#3B82F6] flex-shrink-0" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            <span className="text-sm text-[#9CA3AF]">Gemini is synthesizing {papers.length} papers…</span>
          </div>
        )}

        {/* AI synthesis output */}
        {synthesis && (
          <div className="flex flex-col gap-4">
            {/* Executive summary */}
            <div className="bg-[rgba(59,130,246,0.08)] border border-[rgba(59,130,246,0.2)] rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-[11px] font-semibold text-[#3B82F6] tracking-widest uppercase">Executive Summary</span>
                {synthesis.ai_generated && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-[rgba(34,197,94,0.12)] text-[#22C55E] border border-[rgba(34,197,94,0.3)]">Gemini AI</span>
                )}
                <button onClick={runSynthesis} disabled={synthesizing} className="ml-auto text-[10px] text-[#9CA3AF] hover:text-[#E5E7EB] disabled:opacity-40">↻ Refresh</button>
              </div>
              <p className="text-sm text-[#E5E7EB] leading-relaxed">{synthesis.executive_summary}</p>
            </div>

            {/* Key themes */}
            {synthesis.key_themes.length > 0 && (
              <section>
                <h3 className="text-[13px] font-semibold text-[#E5E7EB] mb-2">Key Themes</h3>
                <div className="space-y-2">
                  {synthesis.key_themes.map((theme, i) => (
                    <div key={i} className="bg-[#1F2933] rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="w-2 h-2 rounded-full bg-[#3B82F6] flex-shrink-0" />
                        <span className="text-[13px] font-semibold text-[#E5E7EB]">{theme.name}</span>
                        {theme.paper_indices.length > 0 && (
                          <span className="ml-auto text-[10px] text-[#9CA3AF]">Papers {theme.paper_indices.slice(0, 4).join(", ")}</span>
                        )}
                      </div>
                      <p className="text-[12px] text-[#9CA3AF] leading-relaxed ml-4">{theme.description}</p>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Research gaps */}
            {synthesis.research_gaps.length > 0 && (
              <section>
                <h3 className="text-[13px] font-semibold text-[#E5E7EB] mb-2">Research Gaps</h3>
                <div className="space-y-2">
                  {synthesis.research_gaps.map((gap, i) => (
                    <div key={i} className="bg-[rgba(249,115,22,0.06)] border border-[rgba(249,115,22,0.2)] rounded-lg p-3">
                      <p className="text-[13px] font-medium text-[#FB923C] mb-1">{gap.gap}</p>
                      <p className="text-[11px] text-[#9CA3AF]"><span className="text-[#E5E7EB]">Evidence: </span>{gap.evidence}</p>
                      <p className="text-[11px] text-[#9CA3AF] mt-0.5"><span className="text-[#E5E7EB]">Impact: </span>{gap.impact}</p>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Open questions */}
            {synthesis.novel_questions.length > 0 && (
              <section>
                <h3 className="text-[13px] font-semibold text-[#E5E7EB] mb-2">Open Research Questions</h3>
                <div className="space-y-1.5">
                  {synthesis.novel_questions.map((q, i) => (
                    <div key={i} className="flex gap-2 text-[12px] text-[#9CA3AF]">
                      <span className="text-[#A78BFA] font-mono flex-shrink-0">Q{i + 1}.</span>
                      <span>{q}</span>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {synthesis.methodology_landscape && (
              <section>
                <h3 className="text-[13px] font-semibold text-[#E5E7EB] mb-1.5">Methodology Landscape</h3>
                <p className="text-[12px] text-[#9CA3AF] leading-relaxed">{synthesis.methodology_landscape}</p>
              </section>
            )}

            {synthesis.contradictions && (
              <section>
                <h3 className="text-[13px] font-semibold text-[#E5E7EB] mb-1.5">Contradictions & Debates</h3>
                <p className="text-[12px] text-[#9CA3AF] leading-relaxed">{synthesis.contradictions}</p>
              </section>
            )}

            <div className="h-px bg-[rgba(148,163,184,0.15)]" />
          </div>
        )}

        {synthError && (
          <p className="text-[12px] text-[#F43F5E] bg-[rgba(244,63,94,0.07)] px-3 py-2 rounded-lg border border-[rgba(244,63,94,0.2)]">{synthError}</p>
        )}

        {/* Papers list */}
        <section>
          <h3 className="text-[13px] font-semibold text-[#E5E7EB] mb-2">Papers ({papers.length})</h3>
          <div className="space-y-2">
            {papers.map((p, i) => (
              <div key={p.paper_id || i} className="bg-[#1F2933] rounded-lg p-3">
                <div className="flex items-start justify-between gap-2">
                  <h4 className="text-sm font-medium leading-snug flex-1">
                    <span className="text-[#9CA3AF]">{i + 1}. </span>
                    <a
                      href={p.doi ? `https://doi.org/${p.doi}` : p.source === "arxiv" ? `https://arxiv.org/abs/${p.paper_id}` : `https://www.semanticscholar.org/paper/${p.paper_id}`}
                      target="_blank" rel="noopener noreferrer"
                      className="text-[#3B82F6] hover:text-[#60A5FA] hover:underline transition-colors"
                    >
                      {p.title}
                    </a>
                  </h4>
                  {p.year && <span className="text-[11px] font-mono text-[#9CA3AF] flex-shrink-0">{p.year}</span>}
                </div>
                {p.authors.length > 0 && (
                  <p className="text-[11px] text-[#9CA3AF] mt-1">
                    {p.authors.slice(0, 3).join(", ")}{p.authors.length > 3 ? " et al." : ""}
                  </p>
                )}
                {p.abstract && (
                  <div>
                    <p className={clsx("text-[12px] text-[#9CA3AF]/80 mt-1.5 leading-relaxed",
                      expandedPaper === (p.paper_id || String(i)) ? "" : "line-clamp-2"
                    )}>{p.abstract}</p>
                    <button
                      onClick={() => setExpandedPaper(expandedPaper === (p.paper_id || String(i)) ? null : (p.paper_id || String(i)))}
                      className="text-[10px] text-[#3B82F6] hover:text-[#60A5FA] mt-0.5"
                    >
                      {expandedPaper === (p.paper_id || String(i)) ? "Show less" : "Read more"}
                    </button>
                  </div>
                )}
                <div className="flex items-center gap-3 mt-2">
                  {p.citation_count !== undefined && (
                    <span className="text-[10px] text-[#9CA3AF]">Citations: <span className="text-[#E5E7EB]">{p.citation_count}</span></span>
                  )}
                  {p.venue && <span className="text-[10px] text-[#9CA3AF] truncate">{p.venue}</span>}
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-[rgba(59,130,246,0.12)] text-[#3B82F6]">{p.source}</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* Sidebar */}
      <aside className="flex flex-col gap-3">
        <div className="bg-[#1F2933] rounded-lg p-4 space-y-3">
          <h4 className="text-[11px] font-semibold text-[#9CA3AF] tracking-widest uppercase">Overview</h4>
          {[
            ["Papers", String(papers.length)],
            ["Themes", String(synthesis?.key_themes?.length || "—")],
            ["Gaps", String(synthesis?.research_gaps?.length || "—")],
            ["Questions", String(synthesis?.novel_questions?.length || "—")],
            ["Source", source === "semantic_scholar" ? "S2" : "arXiv"],
            ["Clusters", String(summary?.num_clusters || 1)],
          ].map(([label, val]) => (
            <div key={label} className="flex justify-between text-sm">
              <span className="text-[#9CA3AF]">{label}</span>
              <span className="font-mono font-medium text-[#E5E7EB]">{val}</span>
            </div>
          ))}
        </div>
        <button onClick={handleDownloadReview} className="w-full py-2 rounded-lg text-xs font-medium border border-[rgba(148,163,184,0.35)] text-[#9CA3AF] hover:text-[#E5E7EB] hover:border-[rgba(148,163,184,0.6)] transition-colors">
          Download full review
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

    const allNodes = results.graph.nodes;
    const allEdges = results.graph.edges;
    if (!allNodes || allNodes.length === 0) return;
    // Include all nodes returned by backend (including external nodes added by Semantic Scholar)
    // to ensure citation edges are visible.
    const realNodes = allNodes;
    const realEdges = allEdges || [];
    const paperById = new Map((results.papers || []).map((p) => [p.paper_id, p]));
    const data = {
      nodes: realNodes.map((n) => {
        const paper = paperById.get(n.id);
        const label = paper?.title ? paper.title.slice(0, 40) + (paper.title.length > 40 ? "…" : "") : n.label;
        return { id: n.id, label, value: n.value || 1, group: paper?.source || n.group || "default",
          title: paper ? `${paper.title}\n${(paper.authors||[]).slice(0,2).join(", ")}\n${paper.year||""} · ${paper.citation_count??0} citations` : n.label };
      }),
      edges: realEdges.map((e) => ({ from: e.from_id, to: e.to_id, value: e.weight || 1, arrows: { to: { enabled: true, scaleFactor: 0.5 } } })),
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
        "external": { color: { background: "#374151", border: "#6B7280" } },
      },
      interaction: { hover: true, zoomView: true },
    };

    const network = new Network(containerRef.current, data, options);
    
    // Disable physics after it settles so nodes don't bounce forever
    network.once("stabilizationIterationsDone", function () {
      network.setOptions({ physics: { enabled: false } });
    });

    networkRef.current = network;

    return () => {
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
function ProposalPane({ results, query, outputLanguage }: { results?: PipelineResults; query?: string; outputLanguage?: string }) {
  const papers = results?.papers || [];
  const years = papers.map((p) => p.year).filter(Boolean) as number[];
  const minYear = years.length > 0 ? Math.min(...years) : 2020;
  const maxYear = years.length > 0 ? Math.max(...years) : 2025;

  const [proposalLatex, setProposalLatex] = useState<string>("");
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (papers.length > 0 && !proposalLatex && !generating) {
      generateProposal();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [results?.session_id]);

  const generateProposal = async () => {
    if (!results || generating) return;
    setGenerating(true);
    setError(null);
    try {
      const res = await fetch("/api/proposal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query || results.session_id,
          papers: results.papers,
          paradigm_shifts: results.paradigm_shifts,
          graph_summary: results.graph_summary,
          timeline: results.timeline,
          output_language: outputLanguage || "en",
        }),
      });
      const data = await res.json();
      if (data.proposal) {
        setProposalLatex(data.proposal);
      } else if (data.latex) {
        setProposalLatex(data.latex);
      } else {
        setError("Proposal generation failed.");
      }
    } catch (_) {
      setError("Failed to generate proposal.");
    } finally {
      setGenerating(false);
    }
  };

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
              disabled={!proposalLatex || generating}
              className="px-3 py-1 rounded border text-[11px] font-medium border-[rgba(148,163,184,0.35)] text-[#9CA3AF] hover:text-[#E5E7EB] hover:border-[rgba(148,163,184,0.6)] transition-colors disabled:opacity-50"
            >
              Copy LaTeX
            </button>
            <button
              onClick={handleOpenOverleaf}
              disabled={!proposalLatex || generating}
              className="px-3 py-1 rounded border text-[11px] font-medium border-[#3B82F6] text-[#3B82F6] hover:bg-[#3B82F6]/10 transition-colors disabled:opacity-50"
            >
              Open in Overleaf
            </button>
          </div>
        </div>

        <div
          className="font-mono text-[12px] text-[#E5E7EB] leading-relaxed p-4 rounded-lg overflow-auto whitespace-pre-wrap relative"
          style={{ backgroundColor: "#1F2933", maxHeight: "400px", minHeight: "200px", border: "1px solid rgba(148,163,184,0.2)" }}
        >
          {generating ? (
            <div className="absolute inset-0 flex items-center justify-center flex-col gap-3 bg-[#1F2933]/80 backdrop-blur-sm z-10">
              <svg className="animate-spin w-6 h-6 text-[#3B82F6]" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span className="text-sm text-[#9CA3AF]">Gemini is drafting your proposal...</span>
            </div>
          ) : error ? (
            <div className="text-[#F43F5E]">{error}</div>
          ) : (
            proposalLatex
          )}
        </div>
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
          disabled={!proposalLatex || generating}
          className="w-full py-2 rounded-lg text-xs font-medium bg-[#3B82F6] text-white hover:bg-[#2563EB] transition-colors disabled:opacity-50"
        >
          Download proposal
        </button>
      </aside>
    </div>
  );
}

// ─── Main ResultsTabs ─────────────────────────────────────────
export function ResultsTabs({ completed, results, query, outputLanguage }: ResultsTabsProps) {
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
              <ReviewPane results={pipelineResults} query={query} outputLanguage={outputLanguage} />
            ) : activeTab === "graph" ? (
              <CitationGraphPane results={pipelineResults} />
            ) : activeTab === "timeline" ? (
              <TimelinePane results={pipelineResults} />
            ) : (
              <ProposalPane results={pipelineResults} query={query} outputLanguage={outputLanguage} />
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  );
}