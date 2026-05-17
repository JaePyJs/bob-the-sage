"""Pytest configuration and shared fixtures.

This module provides common test fixtures, mock data, and utilities
for the SAGE test suite.
"""

import pytest
from typing import Any, Dict, List


# ============================================================================
# Paper Fixtures
# ============================================================================

@pytest.fixture
def sample_papers() -> List[Dict[str, Any]]:
    """Sample paper data for testing."""
    return [
        {
            "paper_id": "p1",
            "title": "CRISPR-Cas9: A Revolutionary Gene Editing Tool",
            "abstract": "This paper introduces CRISPR-Cas9 as a powerful gene editing technology.",
            "authors": ["Jennifer Doudna", "Emmanuelle Charpentier"],
            "year": 2012,
            "primary_category": "q-bio.GN",
            "categories": ["q-bio.GN", "q-bio.MN"],
            "venue": "Science",
            "citation_count": 15000,
            "source": "semantic_scholar",
        },
        {
            "paper_id": "p2",
            "title": "Applications of CRISPR in Medicine",
            "abstract": "Exploring medical applications of CRISPR technology.",
            "authors": ["Feng Zhang", "George Church"],
            "year": 2015,
            "primary_category": "q-bio.GN",
            "categories": ["q-bio.GN"],
            "venue": "Nature Medicine",
            "citation_count": 8000,
            "source": "semantic_scholar",
        },
        {
            "paper_id": "p3",
            "title": "CRISPR Base Editing: Precision Gene Modification",
            "abstract": "Base editing allows precise single-nucleotide changes without double-strand breaks.",
            "authors": ["David Liu"],
            "year": 2016,
            "primary_category": "q-bio.GN",
            "categories": ["q-bio.GN"],
            "venue": "Nature",
            "citation_count": 5000,
            "source": "semantic_scholar",
        },
        {
            "paper_id": "p4",
            "title": "Prime Editing: Next Generation Gene Editing",
            "abstract": "Prime editing enables targeted insertions, deletions, and base conversions.",
            "authors": ["David Liu", "Andrew Anzalone"],
            "year": 2019,
            "primary_category": "q-bio.GN",
            "categories": ["q-bio.GN"],
            "venue": "Nature",
            "citation_count": 3000,
            "source": "semantic_scholar",
        },
        {
            "paper_id": "p5",
            "title": "CRISPR Diagnostics for COVID-19",
            "abstract": "Using CRISPR for rapid COVID-19 detection.",
            "authors": ["Feng Zhang", "Omar Abudayyeh"],
            "year": 2020,
            "primary_category": "q-bio.GN",
            "categories": ["q-bio.GN", "q-bio.QM"],
            "venue": "Science",
            "citation_count": 2000,
            "source": "semantic_scholar",
        },
    ]


@pytest.fixture
def sample_citations() -> List[Dict[str, Any]]:
    """Sample citation data for testing."""
    return [
        {"citing_id": "p2", "cited_id": "p1", "weight": 1.0},
        {"citing_id": "p3", "cited_id": "p1", "weight": 1.0},
        {"citing_id": "p3", "cited_id": "p2", "weight": 0.8},
        {"citing_id": "p4", "cited_id": "p1", "weight": 1.0},
        {"citing_id": "p4", "cited_id": "p2", "weight": 0.7},
        {"citing_id": "p4", "cited_id": "p3", "weight": 0.9},
        {"citing_id": "p5", "cited_id": "p1", "weight": 0.6},
        {"citing_id": "p5", "cited_id": "p2", "weight": 0.8},
    ]


@pytest.fixture
def sample_timeline() -> List[Dict[str, Any]]:
    """Sample timeline data for testing."""
    return [
        {"year": "2012", "papers": 1, "citations": 4},
        {"year": "2013", "papers": 0, "citations": 0},
        {"year": "2014", "papers": 0, "citations": 0},
        {"year": "2015", "papers": 1, "citations": 3},
        {"year": "2016", "papers": 1, "citations": 1},
        {"year": "2017", "papers": 0, "citations": 0},
        {"year": "2018", "papers": 0, "citations": 0},
        {"year": "2019", "papers": 1, "citations": 0},
        {"year": "2020", "papers": 1, "citations": 0},
    ]


# ============================================================================
# arXiv Fixtures
# ============================================================================

@pytest.fixture
def mock_arxiv_papers() -> List[Dict[str, Any]]:
    """Mock arXiv paper data."""
    return [
        {
            "paper_id": "2301.12345",
            "title": "Deep Learning for Protein Structure Prediction",
            "abstract": "We present a novel deep learning approach for protein structure prediction.",
            "authors": ["Alice Smith", "Bob Johnson"],
            "year": 2023,
            "primary_category": "cs.LG",
            "categories": ["cs.LG", "q-bio.BM"],
            "source": "arxiv",
        },
        {
            "paper_id": "2302.67890",
            "title": "Transformer Models in Genomics",
            "abstract": "Applying transformer architectures to genomic sequence analysis.",
            "authors": ["Carol White", "David Brown"],
            "year": 2023,
            "primary_category": "cs.LG",
            "categories": ["cs.LG", "q-bio.GN"],
            "source": "arxiv",
        },
    ]


@pytest.fixture
def mock_arxiv_xml() -> str:
    """Mock arXiv API XML response."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
    <entry>
        <id>http://arxiv.org/abs/2301.12345</id>
        <title>Deep Learning for Protein Structure Prediction</title>
        <summary>We present a novel deep learning approach for protein structure prediction.</summary>
        <author>
            <name>Alice Smith</name>
        </author>
        <author>
            <name>Bob Johnson</name>
        </author>
        <published>2023-01-15T00:00:00Z</published>
        <arxiv:primary_category term="cs.LG"/>
        <category term="cs.LG"/>
        <category term="q-bio.BM"/>
    </entry>
    <entry>
        <id>http://arxiv.org/abs/2302.67890</id>
        <title>Transformer Models in Genomics</title>
        <summary>Applying transformer architectures to genomic sequence analysis.</summary>
        <author>
            <name>Carol White</name>
        </author>
        <author>
            <name>David Brown</name>
        </author>
        <published>2023-02-20T00:00:00Z</published>
        <arxiv:primary_category term="cs.LG"/>
        <category term="cs.LG"/>
        <category term="q-bio.GN"/>
    </entry>
</feed>'''


@pytest.fixture
def mock_arxiv_xml_single() -> str:
    """Mock arXiv API XML response for single paper."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
    <entry>
        <id>http://arxiv.org/abs/2301.12345</id>
        <title>Deep Learning for Protein Structure Prediction</title>
        <summary>We present a novel deep learning approach for protein structure prediction.</summary>
        <author>
            <name>Alice Smith</name>
        </author>
        <published>2023-01-15T00:00:00Z</published>
        <arxiv:primary_category term="cs.LG"/>
        <category term="cs.LG"/>
    </entry>
</feed>'''


# ============================================================================
# Semantic Scholar Fixtures
# ============================================================================

@pytest.fixture
def mock_s2_response() -> Dict[str, Any]:
    """Mock Semantic Scholar API search response."""
    return {
        "data": [
            {
                "paperId": "s2_paper_1",
                "title": "CRISPR Gene Editing",
                "abstract": "A comprehensive review of CRISPR technology.",
                "authors": [{"name": "Jane Doe"}, {"name": "John Smith"}],
                "year": 2020,
                "venue": "Nature",
                "citationCount": 1000,
                "referenceCount": 50,
            },
            {
                "paperId": "s2_paper_2",
                "title": "Applications of Gene Editing",
                "abstract": "Exploring practical applications of gene editing.",
                "authors": [{"name": "Alice Johnson"}],
                "year": 2021,
                "venue": "Science",
                "citationCount": 500,
                "referenceCount": 30,
            },
        ]
    }


@pytest.fixture
def mock_s2_paper_response() -> Dict[str, Any]:
    """Mock Semantic Scholar API single paper response."""
    return {
        "paperId": "s2_paper_1",
        "title": "CRISPR Gene Editing",
        "abstract": "A comprehensive review of CRISPR technology.",
        "authors": [{"name": "Jane Doe"}, {"name": "John Smith"}],
        "year": 2020,
        "venue": "Nature",
        "citationCount": 1000,
    }


@pytest.fixture
def mock_s2_citations_response() -> Dict[str, Any]:
    """Mock Semantic Scholar API citations response."""
    return {
        "data": [
            {
                "citingPaper": {
                    "paperId": "citing_1",
                    "title": "Building on CRISPR",
                    "year": 2021,
                }
            },
            {
                "citingPaper": {
                    "paperId": "citing_2",
                    "title": "CRISPR Applications",
                    "year": 2022,
                }
            },
        ]
    }


# ============================================================================
# Graph Fixtures
# ============================================================================

@pytest.fixture
def sample_graph_nodes() -> List[Dict[str, Any]]:
    """Sample graph nodes for testing."""
    return [
        {"id": "p1", "label": "Paper 1", "group": "cs.AI", "value": 5},
        {"id": "p2", "label": "Paper 2", "group": "cs.AI", "value": 3},
        {"id": "p3", "label": "Paper 3", "group": "cs.LG", "value": 2},
    ]


@pytest.fixture
def sample_graph_edges() -> List[Dict[str, Any]]:
    """Sample graph edges for testing."""
    return [
        {"from_id": "p2", "to_id": "p1", "weight": 1.0},
        {"from_id": "p3", "to_id": "p1", "weight": 0.8},
    ]


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def empty_papers() -> List[Dict[str, Any]]:
    """Empty paper list for edge case testing."""
    return []


@pytest.fixture
def empty_citations() -> List[Dict[str, Any]]:
    """Empty citation list for edge case testing."""
    return []


@pytest.fixture
def malformed_papers() -> List[Dict[str, Any]]:
    """Malformed paper data for error handling tests."""
    return [
        {"title": "No ID Paper"},  # Missing paper_id
        {"paper_id": "p1"},  # Missing other fields
        {"paper_id": "p2", "year": "invalid"},  # Invalid year type
        {"paper_id": "p3", "year": 2020, "title": "Valid Paper"},  # Valid
    ]


@pytest.fixture
def malformed_citations() -> List[Dict[str, Any]]:
    """Malformed citation data for error handling tests."""
    return [
        {"citing_id": "p1"},  # Missing cited_id
        {"cited_id": "p2"},  # Missing citing_id
        {},  # Empty citation
        {"citing_id": "p2", "cited_id": "p1"},  # Valid
    ]


# ============================================================================
# Mock Settings
# ============================================================================

@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    from unittest.mock import Mock
    
    settings = Mock()
    settings.deepl_api_key = None
    settings.semantic_scholar_api_key = None
    settings.allowed_origins = ["http://localhost:3000"]
    settings.arxiv_delay_seconds = 0  # No delay in tests
    settings.s2_requests_per_second = 1
    settings.s2_enabled = False
    
    return settings


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )


# Made with Bob