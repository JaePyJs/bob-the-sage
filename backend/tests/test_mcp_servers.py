"""Tests for MCP server integrations.

This module tests the Semantic Scholar, arXiv, and translation MCP servers
with mocked external API calls. NO live API calls are made.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import asyncio

from backend.mcp_servers import semantic_scholar_mcp, arxiv_mcp


class TestSemanticScholarMCP:
    """Tests for Semantic Scholar MCP server."""

    @pytest.mark.asyncio
    async def test_search_papers_with_api_key(self, mock_s2_response):
        """Test paper search with API key configured."""
        with patch('backend.mcp_servers.semantic_scholar_mcp.settings') as mock_settings:
            mock_settings.s2_enabled = True
            mock_settings.semantic_scholar_api_key = "test-key"
            
            with patch('backend.mcp_servers.semantic_scholar_mcp._s2_get') as mock_get:
                mock_get.return_value = mock_s2_response
                
                result = await semantic_scholar_mcp.search_papers("CRISPR", max_results=10)
                
                assert "papers" in result
                assert "citations" in result
                assert result["source"] == "semantic_scholar"
                assert result["mode"] == "live"
                assert len(result["papers"]) > 0

    @pytest.mark.asyncio
    async def test_search_papers_without_api_key(self, mock_arxiv_papers):
        """Test paper search falls back to arXiv when no API key."""
        with patch('backend.mcp_servers.semantic_scholar_mcp.settings') as mock_settings:
            mock_settings.s2_enabled = False
            
            with patch('backend.mcp_servers.arxiv_mcp.search_arxiv') as mock_arxiv:
                mock_arxiv.return_value = mock_arxiv_papers
                
                result = await semantic_scholar_mcp.search_papers("CRISPR", max_results=10)
                
                assert result["source"] == "arxiv-only"
                assert result["mode"] == "synthetic"
                assert "papers" in result
                assert "citations" in result

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test that rate limiting is enforced (1 RPS)."""
        import time
        
        with patch('backend.mcp_servers.semantic_scholar_mcp._s2_get') as mock_get:
            mock_get.return_value = {"data": []}
            
            # Reset rate limiter
            semantic_scholar_mcp._last_call_ts = 0.0
            
            start = time.monotonic()
            await semantic_scholar_mcp._respect_rate_limit()
            await semantic_scholar_mcp._respect_rate_limit()
            elapsed = time.monotonic() - start
            
            # Second call should wait ~1 second
            assert elapsed >= 1.0

    @pytest.mark.asyncio
    async def test_retry_on_429(self):
        """Test retry logic on rate limit (429) response."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # First call returns 429, second succeeds
            mock_response_429 = Mock()
            mock_response_429.status_code = 429
            
            mock_response_ok = Mock()
            mock_response_ok.status_code = 200
            mock_response_ok.json.return_value = {"data": []}
            
            mock_client.get.side_effect = [
                mock_response_429,
                mock_response_ok,
            ]
            
            with patch('backend.mcp_servers.semantic_scholar_mcp.settings') as mock_settings:
                mock_settings.semantic_scholar_api_key = "test-key"
                
                result = await semantic_scholar_mcp._s2_get("/test")
                
                assert result == {"data": []}
                assert mock_client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test that max retries raises exception."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Always return 429
            mock_response = Mock()
            mock_response.status_code = 429
            mock_client.get.return_value = mock_response
            
            with patch('backend.mcp_servers.semantic_scholar_mcp.settings') as mock_settings:
                mock_settings.semantic_scholar_api_key = "test-key"
                
                with pytest.raises(Exception, match="failed after .* retries"):
                    await semantic_scholar_mcp._s2_get("/test", max_retries=3)

    @pytest.mark.asyncio
    async def test_get_citation_graph(self, mock_s2_paper_response):
        """Test citation graph retrieval."""
        with patch('backend.mcp_servers.semantic_scholar_mcp.settings') as mock_settings:
            mock_settings.s2_enabled = True
            mock_settings.semantic_scholar_api_key = "test-key"
            
            with patch('backend.mcp_servers.semantic_scholar_mcp._s2_get') as mock_get:
                mock_get.return_value = mock_s2_paper_response
                
                result = await semantic_scholar_mcp.get_citation_graph(["paper1", "paper2"])
                
                assert "nodes" in result
                assert "edges" in result
                assert result["mode"] == "live"

    @pytest.mark.asyncio
    async def test_synthetic_citations_generation(self, mock_arxiv_papers):
        """Test synthetic citation generation for fallback mode."""
        citations = semantic_scholar_mcp._generate_synthetic_citations(mock_arxiv_papers)
        
        assert isinstance(citations, list)
        if len(mock_arxiv_papers) >= 2:
            assert len(citations) > 0
            # Check citation structure
            for c in citations:
                assert "citing_id" in c
                assert "cited_id" in c
                assert "weight" in c
                assert 0.0 <= c["weight"] <= 1.0

    @pytest.mark.asyncio
    async def test_synthetic_citations_empty_list(self):
        """Test synthetic citations with empty paper list."""
        citations = semantic_scholar_mcp._generate_synthetic_citations([])
        assert citations == []

    @pytest.mark.asyncio
    async def test_synthetic_citations_single_paper(self):
        """Test synthetic citations with single paper."""
        papers = [{"paper_id": "p1", "year": 2020}]
        citations = semantic_scholar_mcp._generate_synthetic_citations(papers)
        assert citations == []

    @pytest.mark.asyncio
    async def test_search_papers_s2_failure_fallback_to_arxiv(self, mock_arxiv_papers):
        """Test that S2 API failure triggers arXiv fallback."""
        with patch('backend.mcp_servers.semantic_scholar_mcp.settings') as mock_settings:
            mock_settings.s2_enabled = True
            mock_settings.semantic_scholar_api_key = "test-key"
            
            with patch('backend.mcp_servers.semantic_scholar_mcp._s2_get') as mock_get:
                # Simulate S2 API failure
                mock_get.side_effect = Exception("S2 API error")
                
                with patch('backend.mcp_servers.arxiv_mcp.search_arxiv') as mock_arxiv:
                    mock_arxiv.return_value = mock_arxiv_papers
                    
                    result = await semantic_scholar_mcp.search_papers("CRISPR", max_results=10)
                    
                    # Should fall back to arXiv
                    assert result["source"] == "arxiv-only"
                    assert result["mode"] == "synthetic"
                    assert "papers" in result
                    assert "citations" in result

    @pytest.mark.asyncio
    async def test_get_citation_graph_fetch_error_handling(self):
        """Test citation graph handles individual paper fetch errors gracefully."""
        with patch('backend.mcp_servers.semantic_scholar_mcp.settings') as mock_settings:
            mock_settings.s2_enabled = True
            mock_settings.semantic_scholar_api_key = "test-key"
            
            with patch('backend.mcp_servers.semantic_scholar_mcp._s2_get') as mock_get:
                # First paper succeeds, second fails, third succeeds
                mock_get.side_effect = [
                    {"paperId": "p1", "title": "Paper 1", "citations": [], "references": []},
                    Exception("Fetch error"),
                    {"paperId": "p3", "title": "Paper 3", "citations": [], "references": []},
                ]
                
                result = await semantic_scholar_mcp.get_citation_graph(["p1", "p2", "p3"])
                
                # Should have 2 nodes (p1 and p3), p2 skipped due to error
                assert "nodes" in result
                assert "edges" in result
                assert len(result["nodes"]) == 2

    @pytest.mark.asyncio
    async def test_synthetic_citations_temporal_ordering(self):
        """Test synthetic citations respect temporal ordering (newer cites older)."""
        papers = [
            {"paper_id": "p1", "year": 2018},
            {"paper_id": "p2", "year": 2020},
            {"paper_id": "p3", "year": 2022},
        ]
        
        citations = semantic_scholar_mcp._generate_synthetic_citations(papers)
        
        # Verify temporal constraint: citing_year >= cited_year
        for citation in citations:
            citing_paper = next(p for p in papers if p["paper_id"] == citation["citing_id"])
            cited_paper = next(p for p in papers if p["paper_id"] == citation["cited_id"])
            assert citing_paper["year"] >= cited_paper["year"], \
                f"Temporal violation: {citing_paper['year']} citing {cited_paper['year']}"

    @pytest.mark.asyncio
    async def test_synthetic_citations_no_self_citations(self):
        """Test synthetic citations never create self-citations."""
        papers = [
            {"paper_id": "p1", "year": 2020},
            {"paper_id": "p2", "year": 2021},
            {"paper_id": "p3", "year": 2022},
        ]
        
        citations = semantic_scholar_mcp._generate_synthetic_citations(papers)
        
        # Verify no self-citations
        for citation in citations:
            assert citation["citing_id"] != citation["cited_id"], \
                f"Self-citation detected: {citation['citing_id']}"


class TestArxivMCP:
    """Tests for arXiv MCP server."""

    @pytest.mark.asyncio
    async def test_search_arxiv(self, mock_arxiv_xml):
        """Test arXiv search with mocked XML response."""
        with patch('backend.mcp_servers.arxiv_mcp._fetch_url') as mock_fetch:
            mock_fetch.return_value = mock_arxiv_xml
            
            with patch('backend.mcp_servers.arxiv_mcp.settings') as mock_settings:
                mock_settings.arxiv_delay_seconds = 0  # No delay in tests
                
                result = await arxiv_mcp.search_arxiv("CRISPR", max_results=10)
                
                assert isinstance(result, list)
                assert len(result) > 0
                # Check paper structure
                for paper in result:
                    assert "paper_id" in paper
                    assert "title" in paper
                    assert "abstract" in paper
                    assert "authors" in paper
                    assert paper["source"] == "arxiv"

    @pytest.mark.asyncio
    async def test_search_arxiv_with_year_filter(self, mock_arxiv_xml):
        """Test arXiv search with year filtering."""
        with patch('backend.mcp_servers.arxiv_mcp._fetch_url') as mock_fetch:
            mock_fetch.return_value = mock_arxiv_xml
            
            with patch('backend.mcp_servers.arxiv_mcp.settings') as mock_settings:
                mock_settings.arxiv_delay_seconds = 0
                
                result = await arxiv_mcp.search_arxiv(
                    "CRISPR",
                    max_results=10,
                    year_from=2020,
                    year_to=2023
                )
                
                # All papers should be within year range
                for paper in result:
                    if paper.get("year"):
                        assert 2020 <= paper["year"] <= 2023

    @pytest.mark.asyncio
    async def test_search_arxiv_with_categories(self, mock_arxiv_xml):
        """Test arXiv search with category filtering."""
        with patch('backend.mcp_servers.arxiv_mcp._fetch_url') as mock_fetch:
            mock_fetch.return_value = mock_arxiv_xml
            
            with patch('backend.mcp_servers.arxiv_mcp.settings') as mock_settings:
                mock_settings.arxiv_delay_seconds = 0
                
                result = await arxiv_mcp.search_arxiv(
                    "machine learning",
                    max_results=10,
                    categories=["cs.AI", "cs.LG"]
                )
                
                assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_paper_by_id(self, mock_arxiv_xml_single):
        """Test fetching single paper by arXiv ID."""
        with patch('backend.mcp_servers.arxiv_mcp._fetch_url') as mock_fetch:
            mock_fetch.return_value = mock_arxiv_xml_single
            
            result = await arxiv_mcp.get_paper_by_id("2301.12345")
            
            assert result is not None
            assert result["paper_id"] == "2301.12345"
            assert "title" in result
            assert "abstract" in result

    @pytest.mark.asyncio
    async def test_get_paper_by_id_not_found(self):
        """Test fetching non-existent paper returns None."""
        with patch('backend.mcp_servers.arxiv_mcp._fetch_url') as mock_fetch:
            # Empty response
            mock_fetch.return_value = '<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>'
            
            result = await arxiv_mcp.get_paper_by_id("9999.99999")
            
            assert result is None

    def test_parse_arxiv_response(self, mock_arxiv_xml):
        """Test XML parsing of arXiv response."""
        papers = arxiv_mcp._parse_arxiv_response(mock_arxiv_xml)
        
        assert isinstance(papers, list)
        assert len(papers) > 0
        
        # Check first paper structure
        paper = papers[0]
        assert "paper_id" in paper
        assert "title" in paper
        assert "abstract" in paper
        assert "authors" in paper
        assert "year" in paper
        assert "categories" in paper
        assert "primary_category" in paper

    def test_parse_arxiv_response_error_entries(self):
        """Test that error entries are skipped during parsing."""
        xml = '''<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <title>Error</title>
            </entry>
        </feed>'''
        
        papers = arxiv_mcp._parse_arxiv_response(xml)
        assert papers == []

    def test_fetch_url_retry_on_429(self):
        """Test URL fetch retry logic on 429."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            # First call raises 429, second succeeds
            from urllib.error import HTTPError
            
            mock_response = Mock()
            mock_response.read.return_value = b'<feed></feed>'
            
            # Create HTTPError with proper arguments
            error_429 = HTTPError("http://test.com", 429, "Too Many Requests", Mock(), None)
            
            mock_urlopen.side_effect = [
                error_429,
                mock_response,
            ]
            
            with patch('time.sleep'):  # Don't actually sleep in tests
                result = arxiv_mcp._fetch_url("http://test.com")
                
                assert mock_urlopen.call_count == 2

    def test_fetch_url_max_retries(self):
        """Test that max retries raises exception."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            from urllib.error import HTTPError
            
            # Create HTTPError with proper arguments
            error_429 = HTTPError("http://test.com", 429, "Too Many Requests", Mock(), None)
            mock_urlopen.side_effect = error_429
            
            with patch('time.sleep'):
                with pytest.raises(Exception, match="rate limited"):
                    arxiv_mcp._fetch_url("http://test.com", max_retries=3)


class TestTranslationMCP:
    """Tests for translation MCP server (placeholder)."""

    def test_translation_mcp_exists(self):
        """Test that translation MCP module exists."""
        from backend.mcp_servers import translation_mcp
        assert translation_mcp is not None

    # Note: Translation MCP is currently empty, so no functional tests yet
    # Add tests here when translation functionality is implemented


# Made with Bob