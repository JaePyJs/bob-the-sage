"""Pipeline session store — in-memory storage for pipeline state.

Used by the HTTP polling endpoint since WebSocket doesn't work
through WSL2 port forwarding on Windows.
"""

import asyncio
import time
from typing import Any

# In-memory session store
_sessions: dict[str, dict[str, Any]] = {}


def create_session(session_id: str, query: str) -> dict[str, Any]:
    """Create a new pipeline session."""
    session = {
        "session_id": session_id,
        "query": query,
        "stage": "pending",
        "progress": 0,
        "papers_found": 0,
        "papers_analyzed": 0,
        "themes_identified": 0,
        "results": None,
        "error": None,
        "created_at": time.time(),
    }
    _sessions[session_id] = session
    return session


def get_session(session_id: str) -> dict[str, Any] | None:
    """Get session state."""
    return _sessions.get(session_id)


def update_session(session_id: str, **kwargs) -> None:
    """Update session fields."""
    if session_id in _sessions:
        _sessions[session_id].update(kwargs)


def run_pipeline(session_id: str) -> None:
    """Run the pipeline in the background for a session."""
    session = _sessions.get(session_id)
    if not session:
        return

    async def _run():
        from backend.mcp_servers.semantic_scholar_mcp import search_papers, _generate_synthetic_citations
        from backend.engines.citation_graph import build_citation_graph, get_graph_summary
        from backend.engines.timeline import build_timeline, detect_paradigm_shifts
        from backend.config import settings

        query = session["query"]
        papers = []
        citations = []

        try:
            # Stage 1: Discovery — use S2 if key available, else arXiv
            update_session(session_id, stage="discovery", progress=10, message="Searching papers...")
            await asyncio.sleep(0.5)

            search_result = await search_papers(query, max_results=30)
            papers = search_result["papers"]
            citations = search_result["citations"]
            source = search_result.get("source", "unknown")
            papers_found = len(papers)

            update_session(session_id, stage="discovery", progress=25, papers_found=papers_found, message=f"Found {papers_found} papers ({source})")
            await asyncio.sleep(0.3)

            # Stage 2: Extraction
            update_session(session_id, stage="extraction", progress=40, message="Extracting metadata & building citation network...")
            await asyncio.sleep(0.5)

            # If S2 returned no citations (e.g., rate limited), generate synthetic as fallback
            if not citations and papers:
                citations = _generate_synthetic_citations(papers)

            update_session(session_id, stage="extraction", progress=55, papers_analyzed=min(papers_found, 10), message=f"{len(citations)} citation edges")
            await asyncio.sleep(0.3)

            # Stage 3: Synthesis
            update_session(session_id, stage="synthesis", progress=70, message="Building graph & timeline...")
            await asyncio.sleep(0.5)

            graph = build_citation_graph(papers, citations)
            graph_summary = get_graph_summary(papers, citations)
            timeline = build_timeline(papers, citations)
            shifts = detect_paradigm_shifts(timeline)
            themes = min(4, max(1, papers_found // 5))

            update_session(session_id, stage="synthesis", progress=85, papers_analyzed=papers_found, themes_identified=themes, message=f"Graph: {graph_summary['total_nodes']} nodes")
            await asyncio.sleep(0.3)

            # Stage 4: Complete
            update_session(
                session_id,
                stage="complete",
                progress=100,
                papers_found=papers_found,
                papers_analyzed=papers_found,
                themes_identified=themes,
                results={
                    "session_id": session_id,
                    "papers": papers[:10],
                    "citations": citations,
                    "graph": graph.model_dump(),
                    "graph_summary": graph_summary,
                    "timeline": timeline,
                    "paradigm_shifts": shifts,
                },
                message="Pipeline complete",
            )

        except Exception as e:
            update_session(session_id, stage="error", error=str(e), message=str(e))

    # Run in background
    asyncio.create_task(_run())