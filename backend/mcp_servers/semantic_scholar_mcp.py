"""Semantic Scholar MCP wrapper — live API integration.

Uses the Semantic Scholar Graph API with proper rate limiting (1 RPS)
and exponential backoff on 429/timeout responses.

When SEMANTIC_SCHOLAR_API_KEY is set, uses real S2 API.
Otherwise, falls back to synthetic citation generation from arXiv data.
"""

import asyncio
import time
from typing import Any

import httpx

from backend.config import settings

S2_API_BASE = "https://api.semanticscholar.org/graph/v1"

# Rate limiter state
_last_call_ts: float = 0.0
_MIN_INTERVAL = 1.05  # seconds, slightly above 1 RPS


async def _respect_rate_limit() -> None:
    """Enforce 1 RPS rate limit across all S2 calls."""
    global _last_call_ts
    now = time.monotonic()
    elapsed = now - _last_call_ts
    if elapsed < _MIN_INTERVAL:
        await asyncio.sleep(_MIN_INTERVAL - elapsed)
    _last_call_ts = time.monotonic()


async def _s2_get(
    path: str,
    params: dict[str, Any] | None = None,
    max_retries: int = 3,
) -> dict[str, Any]:
    """Make a rate-limited GET request to S2 API with retry/backoff."""
    headers = {}
    if settings.semantic_scholar_api_key:
        headers["x-api-key"] = settings.semantic_scholar_api_key

    url = f"{S2_API_BASE}{path}"

    for attempt in range(max_retries):
        await _respect_rate_limit()

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url, params=params, headers=headers)

            if resp.status_code == 429:
                wait = (attempt + 1) * 2
                await asyncio.sleep(wait)
                continue

            resp.raise_for_status()
            return resp.json()

        except httpx.TimeoutException:
            if attempt < max_retries - 1:
                await asyncio.sleep((attempt + 1) * 2)
                continue
            raise
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (429, 503) and attempt < max_retries - 1:
                await asyncio.sleep((attempt + 1) * 2)
                continue
            raise

    raise Exception(f"S2 API request failed after {max_retries} retries: {url}")


async def search_papers(
    query: str,
    max_results: int = 30,
    year_from: int | None = None,
    year_to: int | None = None,
) -> dict[str, Any]:
    """Search for papers using Semantic Scholar API.

    Returns:
        Dict with 'papers' list and 'citations' list.
    """
    if not settings.s2_enabled:
        # Fallback: arXiv-only mode with synthetic citations
        from backend.mcp_servers.arxiv_mcp import search_arxiv
        from backend.mcp_servers.semantic_scholar_mcp import _generate_synthetic_citations

        papers = await search_arxiv(query, max_results=max_results, year_from=year_from, year_to=year_to)
        citations = _generate_synthetic_citations(papers)
        return {
            "papers": papers,
            "citations": citations,
            "source": "arxiv-only",
            "mode": "synthetic",
        }

    # Build S2 search params
    params: dict[str, Any] = {
        "query": query,
        "limit": min(max_results, 100),
        "fields": "paperId,title,abstract,year,authors,venue,citationCount,referenceCount",
    }
    if year_from or year_to:
        year_range = f"{year_from or 1900}-{year_to or 2030}"
        params["year"] = year_range

    try:
        data = await _s2_get("/paper/search", params=params)
    except Exception:
        # S2 API failed, fall back to arXiv
        from backend.mcp_servers import arxiv_mcp
        
        papers = await arxiv_mcp.search_arxiv(query, max_results=max_results, year_from=year_from, year_to=year_to)
        # Generate synthetic citations for fallback mode
        citations = []
        if len(papers) >= 2:
            import random
            for i, citing_paper in enumerate(papers):
                if i == 0 or not citing_paper.get("year"):
                    continue
                # Each paper cites 1-3 earlier papers
                num_citations = random.randint(1, min(3, i))
                potential_cited = [p for p in papers[:i] if p.get("year", 0) <= citing_paper["year"]]
                cited_papers = random.sample(potential_cited, min(num_citations, len(potential_cited)))
                for cited_paper in cited_papers:
                    citations.append({
                        "citing_id": citing_paper["paper_id"],
                        "cited_id": cited_paper["paper_id"],
                        "weight": random.uniform(0.5, 1.0),
                    })
        return {
            "papers": papers,
            "citations": citations,
            "source": "arxiv-only",
            "mode": "synthetic",
        }

    papers = []
    for p in data.get("data", []):
        papers.append({
            "paper_id": p.get("paperId", ""),
            "title": p.get("title", ""),
            "abstract": p.get("abstract", "") or "",
            "authors": [a.get("name", "") for a in p.get("authors", [])],
            "year": p.get("year"),
            "venue": p.get("venue", ""),
            "citation_count": p.get("citationCount", 0),
            "reference_count": p.get("referenceCount", 0),
            "source": "semantic_scholar",
        })

    # Fetch citations for top papers (limit to avoid rate limit issues)
    citations = []
    top_papers = papers[:10]  # Only fetch citations for top 10 to stay within rate limits
    for p in top_papers:
        try:
            cite_data = await _s2_get(
                f"/paper/{p['paper_id']}/citations",
                params={"fields": "paperId,title,year", "limit": 20},
            )
            for c in cite_data.get("data", []):
                citing = c.get("citingPaper", {})
                if citing:
                    citations.append({
                        "citing_id": citing.get("paperId", ""),
                        "cited_id": p["paper_id"],
                        "weight": 1.0,
                    })
        except Exception:
            # Don't let one failed citation fetch break the whole pipeline
            pass

    return {
        "papers": papers,
        "citations": citations,
        "source": "semantic_scholar",
        "mode": "live",
    }


def _generate_synthetic_citations(
    papers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Generate plausible citation edges from paper metadata (fallback mode)."""
    import random

    if len(papers) < 2:
        return []

    sorted_papers = sorted(papers, key=lambda p: (p.get("year") or 9999, p.get("paper_id", "")))
    citations = []
    paper_ids = [p["paper_id"] for p in sorted_papers]

    for i, later in enumerate(sorted_papers):
        if i == 0:
            continue
        num_citations = min(random.randint(1, 5), i)
        later_cat = later.get("primary_category", later.get("categories", [""])[0] if later.get("categories") else "")
        same_cat_indices = [
            j for j in range(i)
            if (sorted_papers[j].get("primary_category", sorted_papers[j].get("categories", [""])[0] if sorted_papers[j].get("categories") else "") == later_cat)
        ]
        candidate_indices = same_cat_indices if same_cat_indices else list(range(i))
        weights = [1.0 / (i - j + 1) for j in candidate_indices]
        total_w = sum(weights)
        weights = [w / total_w for w in weights]

        cited_indices = set()
        while len(cited_indices) < num_citations and candidate_indices:
            chosen = random.choices(candidate_indices, weights=weights, k=1)[0]
            cited_indices.add(chosen)
            idx = candidate_indices.index(chosen)
            candidate_indices.pop(idx)
            weights.pop(idx)
            if weights:
                total_w = sum(weights)
                weights = [w / total_w for w in weights]

        for j in cited_indices:
            citations.append({
                "citing_id": later["paper_id"],
                "cited_id": sorted_papers[j]["paper_id"],
                "weight": round(random.uniform(0.3, 1.0), 2),
            })

    return citations


async def get_citation_graph(paper_ids: list[str]) -> dict[str, Any]:
    """Get citation graph for a list of paper IDs using S2 API."""
    if not settings.s2_enabled:
        from backend.mcp_servers.arxiv_mcp import get_paper_by_id
        papers = []
        for pid in paper_ids[:20]:
            p = await get_paper_by_id(pid)
            if p:
                papers.append(p)
        citations = _generate_synthetic_citations(papers)
        return {"nodes": papers, "edges": citations, "mode": "synthetic"}

    papers = []
    citations = []

    for pid in paper_ids[:20]:
        try:
            p = await _s2_get(
                f"/paper/{pid}",
                params={"fields": "paperId,title,abstract,year,authors,venue,citationCount"},
            )
            papers.append({
                "paper_id": p.get("paperId", pid),
                "title": p.get("title", ""),
                "abstract": p.get("abstract", "") or "",
                "authors": [a.get("name", "") for a in p.get("authors", [])],
                "year": p.get("year"),
                "venue": p.get("venue", ""),
                "citation_count": p.get("citationCount", 0),
                "source": "semantic_scholar",
            })

            # Fetch citations
            cite_data = await _s2_get(
                f"/paper/{pid}/citations",
                params={"fields": "paperId,title,year", "limit": 10},
            )
            for c in cite_data.get("data", []):
                cited = c.get("citedPaper", {})
                if cited:
                    citations.append({
                        "citing_id": pid,
                        "cited_id": cited.get("paperId", ""),
                        "weight": 1.0,
                    })
        except Exception:
            continue

    return {"nodes": papers, "edges": citations, "mode": "live"}