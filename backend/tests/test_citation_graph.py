"""Tests for citation graph engine.

This module tests the citation graph construction, PageRank computation,
vis.js export format, and graph summary statistics.
"""

import pytest
from backend.engines.citation_graph import (
    build_citation_graph,
    get_graph_summary,
)


class TestBuildCitationGraph:
    """Tests for build_citation_graph function."""

    def test_empty_graph(self):
        """Test that empty inputs return empty graph."""
        result = build_citation_graph([], [])
        
        assert result.nodes == []
        assert result.edges == []

    def test_single_node_no_edges(self):
        """Test graph with single paper and no citations."""
        papers = [
            {
                "paper_id": "p1",
                "title": "Test Paper",
                "year": 2020,
                "primary_category": "cs.AI",
                "authors": ["Alice"],
            }
        ]
        citations = []
        
        result = build_citation_graph(papers, citations)
        
        assert len(result.nodes) == 1
        assert result.nodes[0].id == "p1"
        assert result.nodes[0].label == "Test Paper"
        assert result.nodes[0].group == "cs.AI"
        assert result.nodes[0].value is not None
        assert result.nodes[0].value >= 1  # PageRank scaled value
        assert len(result.edges) == 0

    def test_two_nodes_one_edge(self):
        """Test simple graph with two papers and one citation."""
        papers = [
            {"paper_id": "p1", "title": "Paper 1", "year": 2020},
            {"paper_id": "p2", "title": "Paper 2", "year": 2021},
        ]
        citations = [
            {"citing_id": "p2", "cited_id": "p1", "weight": 0.8}
        ]
        
        result = build_citation_graph(papers, citations)
        
        assert len(result.nodes) == 2
        assert len(result.edges) == 1
        assert result.edges[0].from_id == "p2"
        assert result.edges[0].to_id == "p1"
        assert result.edges[0].weight == 0.8

    def test_disconnected_graph(self):
        """Test graph with disconnected components."""
        papers = [
            {"paper_id": "p1", "title": "Paper 1"},
            {"paper_id": "p2", "title": "Paper 2"},
            {"paper_id": "p3", "title": "Paper 3"},
        ]
        citations = [
            {"citing_id": "p2", "cited_id": "p1"}
        ]
        # p3 is disconnected
        
        result = build_citation_graph(papers, citations)
        
        assert len(result.nodes) == 3
        assert len(result.edges) == 1

    def test_pagerank_computation(self):
        """Test that PageRank is computed and affects node values."""
        papers = [
            {"paper_id": "p1", "title": "Highly Cited"},
            {"paper_id": "p2", "title": "Cites P1"},
            {"paper_id": "p3", "title": "Also Cites P1"},
        ]
        citations = [
            {"citing_id": "p2", "cited_id": "p1"},
            {"citing_id": "p3", "cited_id": "p1"},
        ]
        
        result = build_citation_graph(papers, citations)
        
        # Find p1 (should have higher PageRank due to citations)
        p1_node = next(n for n in result.nodes if n.id == "p1")
        p2_node = next(n for n in result.nodes if n.id == "p2")
        
        # p1 should have higher value (more influential)
        assert p1_node.value is not None
        assert p2_node.value is not None
        assert p1_node.value >= p2_node.value

    def test_missing_paper_id(self):
        """Test that papers without IDs are skipped."""
        papers = [
            {"title": "No ID Paper"},  # Missing paper_id
            {"paper_id": "p1", "title": "Valid Paper"},
        ]
        citations = []
        
        result = build_citation_graph(papers, citations)
        
        assert len(result.nodes) == 1
        assert result.nodes[0].id == "p1"

    def test_dangling_citations_ignored(self):
        """Test that citations to non-existent papers are still included as external nodes."""
        papers = [
            {"paper_id": "p1", "title": "Paper 1"},
        ]
        citations = [
            {"citing_id": "p1", "cited_id": "p999"},  # p999 doesn't exist
            {"citing_id": "p888", "cited_id": "p1"},  # p888 doesn't exist
        ]
        
        result = build_citation_graph(papers, citations)
        
        # Should include original paper + 2 external papers
        assert len(result.nodes) == 3
        # Edges should be created (citing -> cited)
        assert len(result.edges) == 2

    def test_malformed_citations(self):
        """Test that malformed citation records are skipped."""
        papers = [
            {"paper_id": "p1", "title": "Paper 1"},
            {"paper_id": "p2", "title": "Paper 2"},
        ]
        citations = [
            {"citing_id": "p2"},  # Missing cited_id
            {"cited_id": "p1"},  # Missing citing_id
            {},  # Empty citation
            {"citing_id": "p2", "cited_id": "p1"},  # Valid
        ]
        
        result = build_citation_graph(papers, citations)
        
        assert len(result.edges) == 1  # Only valid citation

    def test_title_truncation(self):
        """Test that long titles are truncated for visualization."""
        long_title = "A" * 100
        papers = [
            {"paper_id": "p1", "title": long_title},
        ]
        
        result = build_citation_graph(papers, [])
        
        assert len(result.nodes[0].label) <= 50

    def test_default_category(self):
        """Test that missing category defaults to 'unknown'."""
        papers = [
            {"paper_id": "p1", "title": "Paper 1"},  # No category
        ]
        
        result = build_citation_graph(papers, [])
        
        assert result.nodes[0].group == "unknown"

    def test_weight_clamping(self):
        """Test that edge weights are clamped to [0, 1] range."""
        papers = [
            {"paper_id": "p1", "title": "Paper 1"},
            {"paper_id": "p2", "title": "Paper 2"},
        ]
        citations = [
            {"citing_id": "p2", "cited_id": "p1", "weight": 5.0},  # Too high
        ]
        
        result = build_citation_graph(papers, citations)
        
        # Weight should be clamped to 1.0
        assert result.edges[0].weight is not None
        assert 0.0 <= result.edges[0].weight <= 1.0

    def test_default_weight(self):
        """Test that missing weight defaults to 0.5."""
        papers = [
            {"paper_id": "p1", "title": "Paper 1"},
            {"paper_id": "p2", "title": "Paper 2"},
        ]
        citations = [
            {"citing_id": "p2", "cited_id": "p1"},  # No weight
        ]
        
        result = build_citation_graph(papers, citations)
        
        assert result.edges[0].weight == 0.5

    def test_complex_graph(self):
        """Test a more complex citation network."""
        papers = [
            {"paper_id": f"p{i}", "title": f"Paper {i}", "primary_category": "cs.AI"}
            for i in range(1, 6)
        ]
        citations = [
            {"citing_id": "p2", "cited_id": "p1"},
            {"citing_id": "p3", "cited_id": "p1"},
            {"citing_id": "p3", "cited_id": "p2"},
            {"citing_id": "p4", "cited_id": "p1"},
            {"citing_id": "p5", "cited_id": "p3"},
        ]
        
        result = build_citation_graph(papers, citations)
        
        assert len(result.nodes) == 5
        assert len(result.edges) == 5
        
        # p1 should have highest PageRank (most cited)
        p1_node = next(n for n in result.nodes if n.id == "p1")
        other_values = [n.value for n in result.nodes if n.id != "p1" and n.value is not None]
        assert p1_node.value is not None
        assert len(other_values) > 0
        assert p1_node.value >= max(other_values)


class TestGetGraphSummary:
    """Tests for get_graph_summary function."""

    def test_empty_graph_summary(self):
        """Test summary of empty graph."""
        summary = get_graph_summary([], [])
        
        assert summary["total_nodes"] == 0
        assert summary["total_edges"] == 0
        assert summary["top_cited"] == []
        assert summary["largest_cluster_size"] == 0
        assert summary["num_clusters"] == 0
        assert summary["density"] == 0.0
        assert summary["avg_citations_per_paper"] == 0.0

    def test_single_node_summary(self):
        """Test summary of graph with single node."""
        papers = [{"paper_id": "p1", "title": "Paper 1"}]
        
        summary = get_graph_summary(papers, [])
        
        assert summary["total_nodes"] == 1
        assert summary["total_edges"] == 0
        assert summary["largest_cluster_size"] == 1
        assert summary["num_clusters"] == 1

    def test_top_cited_papers(self):
        """Test that top cited papers are correctly identified."""
        papers = [
            {"paper_id": f"p{i}", "title": f"Paper {i}"}
            for i in range(1, 6)
        ]
        citations = [
            {"citing_id": "p2", "cited_id": "p1"},
            {"citing_id": "p3", "cited_id": "p1"},
            {"citing_id": "p4", "cited_id": "p1"},  # p1 has 3 citations
            {"citing_id": "p3", "cited_id": "p2"},
            {"citing_id": "p4", "cited_id": "p2"},  # p2 has 2 citations
            {"citing_id": "p5", "cited_id": "p3"},  # p3 has 1 citation
        ]
        
        summary = get_graph_summary(papers, citations)
        
        assert len(summary["top_cited"]) <= 5
        # p1 should be most cited
        assert summary["top_cited"][0][0] == "p1"
        assert summary["top_cited"][0][1] == 3

    def test_clustering_analysis(self):
        """Test clustering analysis with disconnected components."""
        papers = [
            {"paper_id": "p1"},
            {"paper_id": "p2"},
            {"paper_id": "p3"},
            {"paper_id": "p4"},
        ]
        citations = [
            {"citing_id": "p2", "cited_id": "p1"},  # Cluster 1: p1-p2
            {"citing_id": "p4", "cited_id": "p3"},  # Cluster 2: p3-p4
        ]
        
        summary = get_graph_summary(papers, citations)
        
        assert summary["num_clusters"] == 2
        assert summary["largest_cluster_size"] == 2

    def test_graph_density(self):
        """Test graph density calculation."""
        papers = [
            {"paper_id": "p1"},
            {"paper_id": "p2"},
            {"paper_id": "p3"},
        ]
        citations = [
            {"citing_id": "p2", "cited_id": "p1"},
            {"citing_id": "p3", "cited_id": "p1"},
            {"citing_id": "p3", "cited_id": "p2"},
        ]
        
        summary = get_graph_summary(papers, citations)
        
        # 3 nodes, 3 edges, max possible = 3*2 = 6
        # density = 3/6 = 0.5
        assert summary["density"] == 0.5

    def test_avg_citations_per_paper(self):
        """Test average citations per paper calculation."""
        papers = [
            {"paper_id": "p1"},
            {"paper_id": "p2"},
            {"paper_id": "p3"},
        ]
        citations = [
            {"citing_id": "p2", "cited_id": "p1"},
            {"citing_id": "p3", "cited_id": "p1"},
        ]
        
        summary = get_graph_summary(papers, citations)
        
        # 2 edges / 3 nodes = 0.67
        assert summary["avg_citations_per_paper"] == 0.67

    def test_invalid_paper_ids_skipped(self):
        """Test that papers without IDs are skipped in summary."""
        papers = [
            {"title": "No ID"},  # Missing paper_id
            {"paper_id": "p1", "title": "Valid"},
        ]
        
        summary = get_graph_summary(papers, [])
        
        assert summary["total_nodes"] == 1

    def test_invalid_citations_skipped(self):
        """Test that invalid citations are skipped in summary."""
        papers = [
            {"paper_id": "p1"},
            {"paper_id": "p2"},
        ]
        citations = [
            {"citing_id": "p2"},  # Missing cited_id
            {},  # Empty
            {"citing_id": "p2", "cited_id": "p1"},  # Valid
        ]
        
        summary = get_graph_summary(papers, citations)
        
        assert summary["total_edges"] == 1


# Made with Bob