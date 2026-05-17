"""Chat endpoint — context-aware AI assistant for SAGE research sessions.

Uses Gemini 2.0 Flash when GEMINI_API_KEY is set; returns structured
data-driven answers when not.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from backend.utils.gemini_client import generate_text, GEMINI_API_KEY

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessage(BaseModel):
    message: str
    session_context: dict = {}  # papers, graph_summary, timeline, paradigm_shifts


@router.post("/message")
async def chat_message(payload: ChatMessage) -> dict:
    """Process a chat message with session context and return a response."""

    ctx = payload.session_context
    papers = ctx.get("papers") or []
    graph = ctx.get("graph_summary") or {}
    shifts = ctx.get("paradigm_shifts") or []
    timeline = ctx.get("timeline") or []

    # Build a compact context summary for the AI
    num_papers = len(papers)
    years = [p["year"] for p in papers if p.get("year")]
    year_range = f"{min(years)}–{max(years)}" if years else "unknown period"

    top_papers_text = "\n".join(
        f"- {p.get('title', 'Unknown')} ({p.get('year', 'n.d.')}) "
        f"by {', '.join((p.get('authors') or [])[:2])}"
        + (f", {p['citation_count']} citations" if p.get("citation_count") else "")
        for p in sorted(papers, key=lambda x: x.get("citation_count") or 0, reverse=True)[:10]
    )

    shifts_text = ""
    if shifts:
        shifts_text = "Paradigm shifts: " + "; ".join(
            f"{s['year']} ({s['growth']}% growth)" for s in shifts[:3]
        )

    if GEMINI_API_KEY and num_papers > 0:
        system = (
            "You are SAGE, an expert AI research assistant. You have access to a systematic literature review "
            f"covering {num_papers} papers from {year_range}. "
            "Answer questions concisely but with specific details from the papers. "
            "When citing papers, use the actual titles. "
            "Keep answers under 200 words unless the user asks for details."
        )

        context_block = f"""SESSION CONTEXT:
- Papers analyzed: {num_papers} ({year_range})
- Citation network: {graph.get('total_nodes', 0)} nodes, {graph.get('total_edges', 0)} edges, {graph.get('num_clusters', 1)} clusters
- {shifts_text}

TOP PAPERS BY CITATION COUNT:
{top_papers_text or 'No papers available.'}"""

        prompt = f"{context_block}\n\nUSER QUESTION: {payload.message}"

        try:
            response = await generate_text(prompt, system=system, max_tokens=512)
            if response.strip():
                return {"response": response, "ai": True}
        except Exception:
            pass

    # Smart template fallback — actually useful answers from the data
    return {"response": _smart_answer(payload.message, papers, graph, shifts, timeline), "ai": False}


def _smart_answer(question: str, papers: list, graph: dict, shifts: list, timeline: list) -> str:
    """Generate a context-aware answer from session data without AI."""
    q = question.lower()
    num_papers = len(papers)

    if not papers:
        return "No papers have been loaded in this session yet. Run a query first to get results."

    years = [p["year"] for p in papers if p.get("year")]
    year_range = f"{min(years)}–{max(years)}" if years else "an unknown period"

    # Papers / how many
    if any(w in q for w in ["how many", "number of paper", "count"]):
        return (
            f"This session analyzed **{num_papers} papers** from {year_range}. "
            f"The citation network contains {graph.get('total_nodes', 0)} nodes and "
            f"{graph.get('total_edges', 0)} edges across {graph.get('num_clusters', 1)} clusters."
        )

    # Most cited
    if any(w in q for w in ["most cited", "top paper", "highly cited", "important paper", "key paper"]):
        top = sorted(papers, key=lambda x: x.get("citation_count") or 0, reverse=True)[:3]
        lines = [f"{i+1}. **{p['title']}** ({p.get('year', 'n.d.')}) — {p.get('citation_count', '?')} citations" for i, p in enumerate(top)]
        return "**Top cited papers in this session:**\n" + "\n".join(lines)

    # Paradigm shifts / trends
    if any(w in q for w in ["trend", "paradigm", "shift", "growth", "change over time"]):
        if shifts:
            shift_strs = [f"**{s['year']}**: {s['growth']}% publication growth" for s in shifts[:3]]
            return "**Paradigm shifts detected:**\n" + "\n".join(shift_strs)
        return f"No significant paradigm shifts detected. Publications remained relatively steady across {year_range}."

    # Timeline / recent
    if any(w in q for w in ["recent", "latest", "newest", "2024", "2025", "2026"]):
        recent = sorted([p for p in papers if p.get("year")], key=lambda x: x["year"], reverse=True)[:3]
        lines = [f"- **{p['title']}** ({p['year']})" for p in recent]
        return "**Most recent papers:**\n" + "\n".join(lines) if lines else "No recent papers found."

    # Authors
    if any(w in q for w in ["author", "who wrote", "researcher"]):
        all_authors: dict[str, int] = {}
        for p in papers:
            for a in (p.get("authors") or []):
                all_authors[a] = all_authors.get(a, 0) + 1
        top_authors = sorted(all_authors.items(), key=lambda x: x[1], reverse=True)[:5]
        if top_authors:
            lines = [f"- **{a}** ({c} paper{'s' if c > 1 else ''})" for a, c in top_authors]
            return "**Most prolific authors in this corpus:**\n" + "\n".join(lines)
        return "Author information is limited in this dataset."

    # Graph / network
    if any(w in q for w in ["graph", "network", "cluster", "citation network", "connected"]):
        return (
            f"The citation network contains **{graph.get('total_nodes', 0)} nodes** and "
            f"**{graph.get('total_edges', 0)} edges**, organized into "
            f"**{graph.get('num_clusters', 1)} clusters**. "
            f"The largest cluster has {graph.get('largest_cluster_size', 1)} papers."
        )

    # Default: summary
    top = sorted(papers, key=lambda x: x.get("citation_count") or 0, reverse=True)[:2]
    top_titles = " and ".join(f'"{p["title"]}"' for p in top) if top else "several papers"
    return (
        f"This session covers **{num_papers} papers** from {year_range}. "
        f"The most influential works include {top_titles}. "
        f"The citation network has {graph.get('total_nodes', 0)} nodes across "
        f"{graph.get('num_clusters', 1)} research clusters. "
        f"Ask me about specific papers, trends, authors, or the citation network!"
    )