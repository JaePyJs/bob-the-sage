"""arXiv MCP server — live API integration.

Uses the official arXiv API (no key required):
  https://export.arxiv.org/api/query

Returns structured paper metadata for SAGE pipeline.
"""

import asyncio
import time
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
from typing import Any

from backend.config import settings

ARXIV_API_BASE = "https://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom",
           "arxiv": "http://arxiv.org/schemas/atom"}
_UA = "SAGE/1.0 (https://github.com/JaePyJs/sage; research tool)"


def _parse_arxiv_response(xml_text: str) -> list[dict[str, Any]]:
    """Parse Atom XML from arXiv API into list of paper dicts."""
    root = ET.fromstring(xml_text)
    papers = []

    for entry in root.findall("atom:entry", ATOM_NS):
        # Skip error entries
        title_el = entry.find("atom:title", ATOM_NS)
        if title_el is None or title_el.text is None:
            continue
        if title_el.text.strip() == "Error":
            continue

        authors = [
            a.find("atom:name", ATOM_NS).text.strip()
            for a in entry.findall("atom:author", ATOM_NS)
            if a.find("atom:name", ATOM_NS) is not None
        ]

        categories = [
            c.get("term", "")
            for c in entry.findall("atom:category", ATOM_NS)
        ]

        primary = entry.find("arxiv:primary_category", ATOM_NS)
        primary_cat = primary.get("term", "") if primary is not None else (categories[0] if categories else "")

        published = entry.find("atom:published", ATOM_NS)
        year = int(published.text[:4]) if published is not None and len(published.text) >= 4 else None

        doi_el = entry.find("arxiv:doi", ATOM_NS)
        doi = doi_el.text.strip() if doi_el is not None else None

        journal_el = entry.find("arxiv:journal_ref", ATOM_NS)
        journal = journal_el.text.strip() if journal_el is not None else None

        summary_el = entry.find("atom:summary", ATOM_NS)
        abstract = (summary_el.text or "").strip().replace("\n", " ") if summary_el is not None else ""

        id_el = entry.find("atom:id", ATOM_NS)
        paper_id = id_el.text.strip().split("/abs/")[-1] if id_el is not None else ""

        paper = {
            "paper_id": paper_id,
            "title": title_el.text.strip().replace("\n", " "),
            "abstract": abstract,
            "authors": authors,
            "year": year,
            "doi": doi,
            "journal": journal,
            "categories": categories,
            "primary_category": primary_cat,
            "source": "arxiv",
        }
        papers.append(paper)

    return papers


def _fetch_url(url: str, max_retries: int = 3) -> str:
    """Fetch URL with retry on 429. Returns response body as string."""
    for attempt in range(max_retries):
        req = urllib.request.Request(url, headers={"User-Agent": _UA})
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            return resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = (attempt + 1) * 5
                time.sleep(wait)
                continue
            raise
    raise Exception(f"arXiv API rate limited after {max_retries} retries")


async def search_arxiv(
    query: str,
    max_results: int = 50,
    year_from: int | None = None,
    year_to: int | None = None,
    categories: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Search arXiv API and return structured paper metadata.

    Date filtering is done post-fetch since arXiv API date range
    syntax is unreliable. We fetch extra results and filter in Python.
    """
    # Build search query — use all: prefix for better matching
    search_terms = [f"all:{t}" for t in query.split() if t]
    if categories:
        cat_query = " OR ".join(f"cat:{c}" for c in categories)
        search_terms.append(f"({cat_query})")

    search_query = " AND ".join(search_terms)

    # Fetch extra to account for year filtering
    fetch_count = min(max_results * 3, 200) if (year_from or year_to) else min(max_results, 200)

    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": fetch_count,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    await asyncio.sleep(settings.arxiv_delay_seconds)
    query_string = urllib.parse.urlencode(params)
    url = f"{ARXIV_API_BASE}?{query_string}"

    xml_text = await asyncio.get_event_loop().run_in_executor(None, _fetch_url, url)
    papers = _parse_arxiv_response(xml_text)

    # Post-filter by year
    if year_from:
        papers = [p for p in papers if p.get("year") and p["year"] >= year_from]
    if year_to:
        papers = [p for p in papers if p.get("year") and p["year"] <= year_to]

    return papers[:max_results]


async def get_paper_by_id(arxiv_id: str) -> dict[str, Any] | None:
    """Fetch a single paper by arXiv ID."""
    params = {"id_list": arxiv_id}
    query_string = urllib.parse.urlencode(params)
    url = f"{ARXIV_API_BASE}?{query_string}"

    xml_text = await asyncio.get_event_loop().run_in_executor(None, _fetch_url, url)
    papers = _parse_arxiv_response(xml_text)
    return papers[0] if papers else None