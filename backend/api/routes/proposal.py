"""Proposal generation route — uses Gemini 2.0 Flash when key is available,
falls back to a high-quality template-based proposal otherwise.
"""

from __future__ import annotations

import json
from fastapi import APIRouter
from pydantic import BaseModel

from backend.utils.gemini_client import generate_text, GEMINI_API_KEY

router = APIRouter(prefix="/api", tags=["proposal"])


class ProposalPayload(BaseModel):
    query: str
    papers: list[dict] = []
    paradigm_shifts: list[dict] = []
    graph_summary: dict = {}
    timeline: list[dict] = []
    output_language: str = "en"  # ISO 639-1 code


@router.post("/generate-proposal")
async def generate_proposal(payload: ProposalPayload) -> dict:
    """Generate an AI research proposal from session data."""

    papers = payload.papers or []
    years = [p["year"] for p in papers if p.get("year")]
    min_year = min(years) if years else 2020
    max_year = max(years) if years else 2025
    num_papers = len(papers)

    # Build rich context from the paper data
    top_papers = papers[:8]
    paper_summaries = []
    for p in top_papers:
        authors = ", ".join((p.get("authors") or [])[:3])
        authors_str = f"{authors} et al." if len(p.get("authors") or []) > 3 else authors
        citation_str = f", {p['citation_count']} citations" if p.get("citation_count") else ""
        abstract_snip = (p.get("abstract") or "")[:300]
        paper_summaries.append(
            f"- **{p.get('title', 'Unknown')}** ({p.get('year', 'n.d.')})"
            f" — {authors_str}{citation_str}.\n  {abstract_snip}"
        )

    shifts_text = ""
    if payload.paradigm_shifts:
        shifts = [
            f"{s['year']}: {s['growth']}% growth ({s['prev_count']} → {s['curr_count']} papers)"
            for s in payload.paradigm_shifts[:3]
        ]
        shifts_text = "Paradigm shifts detected: " + "; ".join(shifts) + "."

    graph = payload.graph_summary
    network_text = (
        f"Citation network: {graph.get('total_nodes', 0)} nodes, "
        f"{graph.get('total_edges', 0)} edges, "
        f"{graph.get('num_clusters', 1)} clusters."
        if graph else ""
    )

    LANG_NAMES = {
        "en": "English", "zh": "Chinese", "ja": "Japanese",
        "es": "Spanish", "de": "German", "fr": "French",
    }
    lang_name = LANG_NAMES.get(payload.output_language, "English")
    lang_instruction = f" Write the proposal in {lang_name}." if payload.output_language != "en" else ""

    system = (
        "You are an expert academic research proposal writer."
        f"{lang_instruction}"
        " Generate a compelling, specific, well-structured research proposal in LaTeX format."
        " Use the actual paper titles, authors, and findings provided — do NOT use generic placeholders."
        " The proposal must be grounded in the real literature provided."
    )

    prompt = f"""Generate a complete LaTeX research proposal based on this systematic literature review:

RESEARCH QUERY: {payload.query}

LITERATURE OVERVIEW:
- {num_papers} papers analyzed from {min_year}–{max_year}
- {network_text}
- {shifts_text}

KEY PAPERS IN THE CORPUS:
{chr(10).join(paper_summaries)}

Generate a complete LaTeX document with these sections:
1. \\section{{Project Background}} — Synthesize the actual research findings above. Reference specific papers by title.
2. \\section{{Research Gaps Identified}} — Identify 3-4 specific gaps based on the literature.
3. \\section{{Proposed Methodology}} — Concrete methods building on techniques found in the papers.
4. \\section{{Timeline}} — Realistic 18-month phased plan.
5. \\section{{Budget Justification}} — Detailed table totaling $250,000–$350,000.
6. \\section{{Expected Impact}} — Specific, measurable outcomes.

Start with \\documentclass{{article}} ... \\begin{{document}} and end with \\end{{document}}.
Make the proposal specific to "{payload.query}" — use exact paper titles and findings."""

    try:
        latex = await generate_text(prompt, system=system, max_tokens=3000)
        if latex.strip():
            return {"latex": latex, "ai_generated": True, "num_papers": num_papers}
    except Exception:
        pass  # Fall through to template

    # High-quality template fallback (when no Gemini key or generation fails)
    # Extract themes from abstracts
    all_text = " ".join(
        (p.get("title") or "") + " " + (p.get("abstract") or "")
        for p in papers[:10]
    ).lower()

    theme_map = {
        "gene editing": ["crispr", "gene edit", "genome edit"],
        "machine learning": ["machine learn", "deep learn", "neural network"],
        "large language models": ["llm", "language model", "gpt", "transformer"],
        "drug discovery": ["drug discov", "therapeut", "pharmacol"],
        "quantum computing": ["quantum", "qubit", "quantum circuit"],
        "clinical research": ["clinical trial", "patient", "randomized"],
    }

    themes = [t for t, kws in theme_map.items() if any(kw in all_text for kw in kws)]
    if not themes:
        themes = ["emerging methodologies in the field"]

    gaps = _identify_gaps(papers, payload.paradigm_shifts, graph)

    latex = _build_template_proposal(
        query=payload.query,
        papers=papers,
        top_papers=top_papers,
        themes=themes,
        gaps=gaps,
        min_year=min_year,
        max_year=max_year,
        shifts_text=shifts_text,
        network_text=network_text,
    )

    return {"latex": latex, "ai_generated": False, "num_papers": num_papers}


def _identify_gaps(papers, shifts, graph):
    gaps = []
    years = [p["year"] for p in papers if p.get("year")]
    max_year = max(years) if years else 2025
    recent = [p for p in papers if p.get("year") and p["year"] >= max_year - 2]
    if len(recent) < len(papers) * 0.3:
        gaps.append("Scarcity of recent empirical validation studies (last 2 years)")
    all_text = " ".join((p.get("abstract") or "") for p in papers).lower()
    if "limitation" in all_text or "future work" in all_text:
        gaps.append("Methodological limitations acknowledged across multiple studies")
    if graph.get("num_clusters", 0) > 3:
        gaps.append(f"Fragmented research landscape ({graph['num_clusters']} distinct clusters) with limited cross-disciplinary synthesis")
    if not gaps:
        gaps = [
            "Lack of large-scale longitudinal studies",
            "Absence of standardized evaluation benchmarks",
            "Limited real-world validation beyond controlled settings",
        ]
    return gaps[:4]


def _build_template_proposal(query, papers, top_papers, themes, gaps, min_year, max_year, shifts_text, network_text):
    theme_str = ", ".join(themes[:2]) if themes else "emerging research"
    num_papers = len(papers)

    citations_block = "\n".join(
        f"  \\item {p.get('title', 'Unknown')} ({p.get('year', 'n.d.')})"
        + (f" — {', '.join((p.get('authors') or [])[:2])}" if p.get("authors") else "")
        for p in top_papers[:5]
    )

    gaps_block = "\n".join(f"  \\item {g}" for g in gaps)

    high_cited = sorted(
        [p for p in papers if p.get("citation_count")],
        key=lambda p: p.get("citation_count", 0),
        reverse=True,
    )[:3]

    ref_block = "\n".join(
        f"  \\item {p.get('title', 'Unknown')}. "
        + ", ".join((p.get("authors") or [])[:3])
        + f" ({p.get('year', 'n.d.')})."
        + (f" {p.get('citation_count')} citations." if p.get("citation_count") else "")
        for p in high_cited
    ) or "  \\item No references available."

    return f"""\\documentclass{{article}}
\\usepackage{{geometry}}
\\geometry{{margin=1in}}
\\usepackage{{booktabs}}
\\usepackage{{hyperref}}

\\title{{Research Proposal: Advancing {themes[0].title() if themes else query[:50]}}}
\\author{{Generated by SAGE}}
\\date{{\\today}}

\\begin{{document}}
\\maketitle

\\section{{Project Background}}

This proposal is grounded in a systematic review of \\textbf{{{num_papers} peer-reviewed publications}} spanning {min_year}--{max_year} on the topic: \\textit{{{query}}}. {network_text} {shifts_text}

The corpus reveals a rapidly evolving field with significant advances in {theme_str}. Key contributing works include:

\\begin{{itemize}}
{citations_block}
\\end{{itemize}}

Analysis of the citation network reveals interconnected clusters of research activity, suggesting both consolidation of foundational methods and emerging frontiers requiring dedicated investigation.

\\section{{Research Gaps Identified}}

Based on systematic analysis of {num_papers} papers and their citation relationships, the following gaps warrant dedicated research:

\\begin{{itemize}}
{gaps_block}
\\end{{itemize}}

\\section{{Proposed Methodology}}

Building on methodologies identified in the literature review, this study proposes a mixed-methods approach:

\\begin{{enumerate}}
  \\item \\textbf{{Phase 1 — Systematic Review \\& Framework Development:}} Conduct a meta-analysis of existing approaches, establishing standardized evaluation criteria derived from the {num_papers}-paper corpus.
  \\item \\textbf{{Phase 2 — Empirical Investigation:}} Design and execute controlled experiments addressing the identified gaps, with study designs informed by highest-cited works in the corpus.
  \\item \\textbf{{Phase 3 — Validation \\& Dissemination:}} Independent replication of key findings, followed by publication and open-source release of datasets and tools.
\\end{{enumerate}}

\\section{{Timeline}}

\\textbf{{Phase 1 (Months 1--6):}} Literature synthesis, framework design, IRB/ethics approval, team recruitment.

\\textbf{{Phase 2 (Months 7--14):}} Data collection, experimental execution, iterative analysis with mid-point review.

\\textbf{{Phase 3 (Months 15--18):}} Validation studies, manuscript preparation, conference presentations, data release.

\\section{{Budget Justification}}

\\begin{{tabular}}{{lr}}
\\toprule
\\textbf{{Category}} & \\textbf{{Amount}} \\\\
\\midrule
Personnel (PI, 2 postdocs, 1 RA) & \\$165,000 \\\\
Research computing \\& infrastructure & \\$40,000 \\\\
Data acquisition \\& licensing & \\$25,000 \\\\
Equipment \\& laboratory supplies & \\$30,000 \\\\
Dissemination (conferences, OA fees) & \\$15,000 \\\\
Contingency (10\\%) & \\$25,000 \\\\
\\midrule
\\textbf{{Total}} & \\textbf{{\\$300,000}} \\\\
\\bottomrule
\\end{{tabular}}

\\section{{Expected Impact}}

This research addresses critical gaps identified in the {min_year}--{max_year} literature on {query}. Expected outcomes include:

\\begin{{itemize}}
  \\item \\textbf{{Scientific:}} 3--5 peer-reviewed publications in high-impact venues; novel insights advancing {theme_str}.
  \\item \\textbf{{Practical:}} Open-source tools and datasets enabling reproducibility; evidence-based recommendations for practitioners.
  \\item \\textbf{{Community:}} Bridging the {len(gaps)}-gap research agenda identified through systematic review of {num_papers} papers.
\\end{{itemize}}

\\section{{Key References}}

\\begin{{itemize}}
{ref_block}
\\end{{itemize}}

\\end{{document}}"""