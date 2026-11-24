import asyncio

import httpx
import pytest
import pytest_asyncio

from backend.config import settings
from backend.main import app
from backend.mcp_servers import semantic_scholar_mcp


@pytest_asyncio.fixture
async def client():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client


@pytest.fixture
def papers():
    return [
        {
            "paper_id": "foundation",
            "title": "Attention in Neural Translation",
            "abstract": "A method for training a neural network.",
            "authors": ["Alan Day", "Jo Chen", "Sam Lee", "Kim Bell"],
            "year": 2017,
            "citation_count": 11,
        },
        {
            "paper_id": "follow-up",
            "title": "A Transformer for Text Translation",
            "abstract": "We compare training approaches and discuss limitations.",
            "year": 2019,
            "citation_count": 1,
        },
    ]


@pytest.fixture
def no_gemini_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(settings, "gemini_api_key", None)


async def wait_for_results(client, session_id):
    async with asyncio.timeout(10):
        while True:
            response = await client.get(f"/api/pipeline/{session_id}")
            response.raise_for_status()
            state = response.json()
            if state["stage"] in {"complete", "error"}:
                return state
            await asyncio.sleep(0.05)


async def test_query_publishes_citation_graph_and_timeline(client, papers, monkeypatch):
    async def search_papers(query, *, max_results, categories):
        assert (query, max_results, categories) == ("attention", 2, ["cs.CL"])
        return {
            "papers": papers,
            "citations": [{"citing_id": "follow-up", "cited_id": "foundation"}],
        }

    monkeypatch.setattr(semantic_scholar_mcp, "search_papers", search_papers)
    response = await client.post(
        "/api/query",
        json={"query": "attention", "max_papers": 2, "disciplines": ["cs.CL"]},
    )
    response.raise_for_status()
    state = await wait_for_results(client, response.json()["session_id"])

    assert state["stage"] == "complete"
    assert state["progress"] == 100
    result = state["results"]
    assert result["graph"]["edges"] == [
        {"from_id": "follow-up", "to_id": "foundation", "weight": 0.5},
    ]
    assert result["timeline"] == [
        {"year": "2017", "papers": 1, "citations": 1},
        {"year": "2018", "papers": 0, "citations": 0},
        {"year": "2019", "papers": 1, "citations": 0},
    ]


async def test_query_reports_a_provider_failure_without_partial_results(client, monkeypatch):
    async def unavailable(*_args, **_kwargs):
        raise httpx.ConnectError("Paper service unavailable")

    monkeypatch.setattr(semantic_scholar_mcp, "search_papers", unavailable)
    response = await client.post("/api/query", json={"query": "attention"})
    response.raise_for_status()
    state = await wait_for_results(client, response.json()["session_id"])

    assert state["stage"] == "error"
    assert state["error"] == "Paper service unavailable"
    assert state["results"] is None


async def test_synthesis_marks_the_keyword_summary_as_non_ai(client, papers, no_gemini_key):
    response = await client.post("/api/synthesize", json={"query": "attention", "papers": papers})
    response.raise_for_status()
    synthesis = response.json()

    assert synthesis["ai_generated"] is False
    assert synthesis["year_range"] == "2017–2019"
    machine_learning = next(theme for theme in synthesis["key_themes"] if theme["name"] == "Machine Learning")
    assert machine_learning["paper_indices"] == [1, 2]


async def test_proposal_template_keeps_corpus_details_when_gemini_is_unavailable(client, papers, no_gemini_key):
    response = await client.post(
        "/api/generate-proposal",
        json={
            "query": "attention in translation",
            "papers": papers,
            "graph_summary": {"total_nodes": 2, "total_edges": 1, "num_clusters": 1},
        },
    )
    response.raise_for_status()
    proposal = response.json()

    assert proposal["ai_generated"] is False
    assert proposal["num_papers"] == 2
    latex = proposal["latex"]
    assert latex.startswith(r"\documentclass{article}")
    assert latex.rstrip().endswith(r"\end{document}")
    assert "attention in translation" in latex
    assert "Attention in Neural Translation" in latex
    assert "Citation network: 2 nodes, 1 edges, 1 clusters." in latex
