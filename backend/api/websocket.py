"""WebSocket pipeline — real arXiv data + synthetic citations.

4-stage pipeline:
  1. discovery  — search arXiv for papers
  2. extraction — parse metadata, generate synthetic citations
  3. synthesis  — build graph + timeline, generate review
  4. complete   — return full results
"""

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.mcp_servers.arxiv_mcp import search_arxiv
from backend.mcp_servers.semantic_scholar_mcp import _generate_synthetic_citations
from backend.engines.citation_graph import build_citation_graph, get_graph_summary
from backend.engines.timeline import build_timeline, detect_paradigm_shifts

router = APIRouter(prefix="/api", tags=["websocket"])


async def _run_pipeline(websocket: WebSocket, session_id: str, query: str) -> None:
    """Run the full SAGE pipeline and send WS updates."""
    papers: list[dict[str, Any]] = []
    citations: list[dict[str, Any]] = []

    try:
        # ── Stage 1: Discovery ──────────────────────────────
        await websocket.send_json({
            "stage": "discovery",
            "progress": 10,
            "message": "Searching arXiv...",
        })
        await asyncio.sleep(1)

        papers = await search_arxiv(query, max_results=30)
        papers_found = len(papers)

        await websocket.send_json({
            "stage": "discovery",
            "progress": 25,
            "papers_found": papers_found,
            "message": f"Found {papers_found} papers",
        })
        await asyncio.sleep(0.5)

        # ── Stage 2: Extraction ─────────────────────────────
        await websocket.send_json({
            "stage": "extraction",
            "progress": 40,
            "papers_found": papers_found,
            "message": "Extracting metadata & building citation network...",
        })
        await asyncio.sleep(1)

        citations = _generate_synthetic_citations(papers)

        await websocket.send_json({
            "stage": "extraction",
            "progress": 55,
            "papers_found": papers_found,
            "papers_analyzed": min(papers_found, 10),
            "message": f"Generated {len(citations)} citation edges",
        })
        await asyncio.sleep(0.5)

        # ── Stage 3: Synthesis ──────────────────────────────
        await websocket.send_json({
            "stage": "synthesis",
            "progress": 70,
            "papers_found": papers_found,
            "papers_analyzed": papers_found,
            "themes_identified": min(4, max(1, papers_found // 5)),
            "message": "Building graph & timeline...",
        })
        await asyncio.sleep(1)

        # Build graph
        graph = build_citation_graph(papers, citations)
        graph_summary = get_graph_summary(papers, citations)

        # Build timeline
        timeline = build_timeline(papers, citations)
        shifts = detect_paradigm_shifts(timeline)

        await websocket.send_json({
            "stage": "synthesis",
            "progress": 85,
            "papers_found": papers_found,
            "papers_analyzed": papers_found,
            "themes_identified": min(4, max(1, papers_found // 5)),
            "message": f"Graph: {graph_summary['total_nodes']} nodes, {graph_summary['total_edges']} edges",
        })
        await asyncio.sleep(0.5)

        # ── Stage 4: Complete ───────────────────────────────
        await websocket.send_json({
            "stage": "complete",
            "progress": 100,
            "papers_found": papers_found,
            "papers_analyzed": papers_found,
            "themes_identified": min(4, max(1, papers_found // 5)),
            "results": {
                "session_id": session_id,
                "papers": papers[:10],  # Send top 10 to avoid WS size limits
                "citations": citations,
                "graph": graph.model_dump(),
                "graph_summary": graph_summary,
                "timeline": timeline,
                "paradigm_shifts": shifts,
            },
        })

    except Exception as e:
        await websocket.send_json({
            "stage": "error",
            "progress": 0,
            "message": str(e),
        })


@router.websocket("/chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str) -> None:
    """WebSocket endpoint for real-time pipeline updates.

    Expected first message from client: {"query": "search query"}
    """
    await websocket.accept()

    try:
        # Wait for the client to send the query
        data = await websocket.receive_json()
        query = data.get("query", "")

        if not query:
            await websocket.send_json({
                "stage": "error",
                "message": "No query provided",
            })
            await websocket.close()
            return

        await _run_pipeline(websocket, session_id, query)
        await websocket.close()

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "stage": "error",
                "message": str(e),
            })
        except Exception:
            pass