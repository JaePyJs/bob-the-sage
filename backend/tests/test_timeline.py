"""Tests for timeline engine.

This module tests timeline construction, gap filling, paradigm shift detection,
and timeline summary statistics.
"""

import pytest
from backend.engines.timeline import (
    build_timeline,
    detect_paradigm_shifts,
    get_timeline_summary,
)


class TestBuildTimeline:
    """Tests for build_timeline function."""

    def test_empty_timeline(self):
        """Test that empty inputs return empty timeline."""
        result = build_timeline([], [])
        assert result == []

    def test_single_paper_single_year(self):
        """Test timeline with single paper."""
        papers = [
            {"paper_id": "p1", "title": "Paper 1", "year": 2020}
        ]
        citations = []
        
        result = build_timeline(papers, citations)
        
        assert len(result) == 1
        assert result[0]["year"] == "2020"
        assert result[0]["papers"] == 1
        assert result[0]["citations"] == 0

    def test_multiple_papers_same_year(self):
        """Test multiple papers in same year."""
        papers = [
            {"paper_id": "p1", "year": 2020},
            {"paper_id": "p2", "year": 2020},
            {"paper_id": "p3", "year": 2020},
        ]
        
        result = build_timeline(papers, [])
        
        assert len(result) == 1
        assert result[0]["papers"] == 3

    def test_gap_filling(self):
        """Test that gaps in years are filled with zeros."""
        papers = [
            {"paper_id": "p1", "year": 2020},
            {"paper_id": "p2", "year": 2022},  # Gap: 2021 missing
        ]
        
        result = build_timeline(papers, [])
        
        assert len(result) == 3  # 2020, 2021, 2022
        assert result[0]["year"] == "2020"
        assert result[0]["papers"] == 1
        assert result[1]["year"] == "2021"
        assert result[1]["papers"] == 0  # Gap filled
        assert result[2]["year"] == "2022"
        assert result[2]["papers"] == 1

    def test_citation_attribution(self):
        """Test that citations are attributed to cited paper's year."""
        papers = [
            {"paper_id": "p1", "year": 2020},
            {"paper_id": "p2", "year": 2021},
        ]
        citations = [
            {"citing_id": "p2", "cited_id": "p1"}  # p2 cites p1
        ]
        
        result = build_timeline(papers, citations)
        
        # Citation should be attributed to p1's year (2020)
        year_2020 = next(t for t in result if t["year"] == "2020")
        assert year_2020["citations"] == 1

    def test_multiple_citations_same_year(self):
        """Test multiple citations to papers in same year."""
        papers = [
            {"paper_id": "p1", "year": 2020},
            {"paper_id": "p2", "year": 2020},
            {"paper_id": "p3", "year": 2021},
        ]
        citations = [
            {"citing_id": "p3", "cited_id": "p1"},
            {"citing_id": "p3", "cited_id": "p2"},
        ]
        
        result = build_timeline(papers, citations)
        
        year_2020 = next(t for t in result if t["year"] == "2020")
        assert year_2020["citations"] == 2

    def test_papers_without_year_excluded(self):
        """Test that papers without year metadata are excluded."""
        papers = [
            {"paper_id": "p1", "year": 2020},
            {"paper_id": "p2"},  # No year
            {"paper_id": "p3", "year": None},  # Explicit None
        ]
        
        result = build_timeline(papers, [])
        
        assert len(result) == 1
        assert result[0]["papers"] == 1

    def test_invalid_year_excluded(self):
        """Test that papers with invalid years are excluded."""
        papers = [
            {"paper_id": "p1", "year": 2020},
            {"paper_id": "p2", "year": 1800},  # Too old
            {"paper_id": "p3", "year": 2200},  # Too far future
            {"paper_id": "p4", "year": "invalid"},  # Not an int
        ]
        
        result = build_timeline(papers, [])
        
        assert len(result) == 1
        assert result[0]["papers"] == 1

    def test_year_as_string(self):
        """Test that years are returned as strings for JSON serialization."""
        papers = [{"paper_id": "p1", "year": 2020}]
        
        result = build_timeline(papers, [])
        
        assert isinstance(result[0]["year"], str)
        assert result[0]["year"] == "2020"

    def test_citations_to_missing_papers_ignored(self):
        """Test that citations to non-existent papers are ignored."""
        papers = [
            {"paper_id": "p1", "year": 2020},
        ]
        citations = [
            {"citing_id": "p1", "cited_id": "p999"},  # p999 doesn't exist
        ]
        
        result = build_timeline(papers, citations)
        
        assert result[0]["citations"] == 0

    def test_sparse_timeline(self):
        """Test timeline with large gaps."""
        papers = [
            {"paper_id": "p1", "year": 2000},
            {"paper_id": "p2", "year": 2010},
        ]
        
        result = build_timeline(papers, [])
        
        assert len(result) == 11  # 2000-2010 inclusive
        # Check that middle years have zero papers
        middle_years = [t for t in result if t["year"] not in ["2000", "2010"]]
        assert all(t["papers"] == 0 for t in middle_years)


class TestDetectParadigmShifts:
    """Tests for detect_paradigm_shifts function."""

    def test_empty_timeline(self):
        """Test that empty timeline returns no shifts."""
        result = detect_paradigm_shifts([])
        assert result == []

    def test_single_year_timeline(self):
        """Test that single year timeline returns no shifts."""
        timeline = [{"year": "2020", "papers": 10, "citations": 5}]
        
        result = detect_paradigm_shifts(timeline)
        
        assert result == []

    def test_no_shifts_detected(self):
        """Test timeline with steady growth (no paradigm shifts)."""
        timeline = [
            {"year": "2020", "papers": 10, "citations": 5},
            {"year": "2021", "papers": 12, "citations": 8},  # 20% growth
            {"year": "2022", "papers": 14, "citations": 10},  # 17% growth
        ]
        
        result = detect_paradigm_shifts(timeline)
        
        assert result == []  # No 100%+ growth

    def test_paradigm_shift_detected(self):
        """Test detection of significant growth (paradigm shift)."""
        timeline = [
            {"year": "2020", "papers": 5, "citations": 10},
            {"year": "2021", "papers": 12, "citations": 25},  # 140% growth
        ]
        
        result = detect_paradigm_shifts(timeline)
        
        assert len(result) == 1
        assert result[0]["year"] == "2021"
        assert result[0]["growth"] == 140
        assert result[0]["prev_count"] == 5
        assert result[0]["curr_count"] == 12

    def test_multiple_shifts(self):
        """Test detection of multiple paradigm shifts."""
        timeline = [
            {"year": "2018", "papers": 3, "citations": 5},
            {"year": "2019", "papers": 7, "citations": 10},  # 133% growth
            {"year": "2020", "papers": 8, "citations": 15},  # 14% growth
            {"year": "2021", "papers": 20, "citations": 40},  # 150% growth
        ]
        
        result = detect_paradigm_shifts(timeline)
        
        assert len(result) == 2
        assert result[0]["year"] == "2019"
        assert result[1]["year"] == "2021"

    def test_custom_threshold(self):
        """Test paradigm shift detection with custom threshold."""
        timeline = [
            {"year": "2020", "papers": 10, "citations": 5},
            {"year": "2021", "papers": 18, "citations": 8},  # 80% growth
        ]
        
        # Default threshold (2.0 = 100%) - no shift
        result_default = detect_paradigm_shifts(timeline)
        assert len(result_default) == 0
        
        # Lower threshold (1.5 = 50%) - shift detected
        result_custom = detect_paradigm_shifts(timeline, growth_threshold=1.5)
        assert len(result_custom) == 1

    def test_min_baseline_filter(self):
        """Test that minimum baseline filter prevents false positives."""
        timeline = [
            {"year": "2020", "papers": 1, "citations": 0},
            {"year": "2021", "papers": 5, "citations": 2},  # 400% growth but from 1 paper
        ]
        
        # Default min_baseline=2 - no shift (baseline too low)
        result_default = detect_paradigm_shifts(timeline)
        assert len(result_default) == 0
        
        # Lower min_baseline=1 - shift detected
        result_custom = detect_paradigm_shifts(timeline, min_baseline=1)
        assert len(result_custom) == 1

    def test_zero_previous_count_ignored(self):
        """Test that years with zero previous count are ignored."""
        timeline = [
            {"year": "2020", "papers": 0, "citations": 0},
            {"year": "2021", "papers": 10, "citations": 5},
        ]
        
        result = detect_paradigm_shifts(timeline)
        
        assert result == []  # Can't calculate growth from zero

    def test_malformed_data_skipped(self):
        """Test that malformed timeline entries are skipped."""
        timeline = [
            {"year": "2020", "papers": 5},  # Missing citations (ok)
            {"year": "2021", "papers": "invalid"},  # Invalid type
            {"year": "2022", "papers": 10},
        ]
        
        result = detect_paradigm_shifts(timeline)
        
        # Should skip 2021 due to invalid data
        assert len(result) == 0

    def test_exact_threshold_match(self):
        """Test that exact threshold match is detected."""
        timeline = [
            {"year": "2020", "papers": 5, "citations": 10},
            {"year": "2021", "papers": 10, "citations": 20},  # Exactly 100% growth
        ]
        
        result = detect_paradigm_shifts(timeline, growth_threshold=2.0)
        
        assert len(result) == 1
        assert result[0]["growth"] == 100


class TestGetTimelineSummary:
    """Tests for get_timeline_summary function."""

    def test_empty_timeline_summary(self):
        """Test summary of empty timeline."""
        summary = get_timeline_summary([])
        
        assert summary["total_papers"] == 0
        assert summary["total_citations"] == 0
        assert summary["year_range"] is None
        assert summary["avg_papers_per_year"] == 0.0
        assert summary["avg_citations_per_year"] == 0.0
        assert summary["peak_year"] is None
        assert summary["peak_papers"] == 0
        assert summary["growth_rate"] is None

    def test_single_year_summary(self):
        """Test summary of single year timeline."""
        timeline = [
            {"year": "2020", "papers": 10, "citations": 25}
        ]
        
        summary = get_timeline_summary(timeline)
        
        assert summary["total_papers"] == 10
        assert summary["total_citations"] == 25
        assert summary["year_range"] == ("2020", "2020")
        assert summary["avg_papers_per_year"] == 10.0
        assert summary["peak_year"] == "2020"
        assert summary["peak_papers"] == 10
        assert summary["growth_rate"] is None  # Need multiple years

    def test_multi_year_summary(self):
        """Test summary of multi-year timeline."""
        timeline = [
            {"year": "2020", "papers": 5, "citations": 10},
            {"year": "2021", "papers": 8, "citations": 15},
            {"year": "2022", "papers": 12, "citations": 30},
        ]
        
        summary = get_timeline_summary(timeline)
        
        assert summary["total_papers"] == 25
        assert summary["total_citations"] == 55
        assert summary["year_range"] == ("2020", "2022")
        assert summary["avg_papers_per_year"] == 8.33
        assert summary["avg_citations_per_year"] == 18.33
        assert summary["peak_year"] == "2022"
        assert summary["peak_papers"] == 12

    def test_growth_rate_calculation(self):
        """Test CAGR (Compound Annual Growth Rate) calculation."""
        timeline = [
            {"year": "2020", "papers": 10, "citations": 20},
            {"year": "2021", "papers": 20, "citations": 40},  # 100% growth
        ]
        
        summary = get_timeline_summary(timeline)
        
        # CAGR = (20/10)^(1/1) - 1 = 1.0 = 100%
        assert summary["growth_rate"] == 100.0

    def test_growth_rate_multi_year(self):
        """Test CAGR over multiple years."""
        timeline = [
            {"year": "2020", "papers": 10, "citations": 20},
            {"year": "2021", "papers": 15, "citations": 30},
            {"year": "2022", "papers": 22, "citations": 45},
        ]
        
        summary = get_timeline_summary(timeline)
        
        # CAGR = (22/10)^(1/2) - 1 ≈ 0.483 = 48.3%
        assert summary["growth_rate"] is not None
        assert 48 <= summary["growth_rate"] <= 49

    def test_growth_rate_with_zero_start(self):
        """Test that growth rate is None when starting from zero."""
        timeline = [
            {"year": "2020", "papers": 0, "citations": 0},
            {"year": "2021", "papers": 10, "citations": 20},
        ]
        
        summary = get_timeline_summary(timeline)
        
        assert summary["growth_rate"] is None

    def test_peak_year_identification(self):
        """Test that peak year is correctly identified."""
        timeline = [
            {"year": "2020", "papers": 5, "citations": 10},
            {"year": "2021", "papers": 15, "citations": 30},  # Peak
            {"year": "2022", "papers": 10, "citations": 25},
        ]
        
        summary = get_timeline_summary(timeline)
        
        assert summary["peak_year"] == "2021"
        assert summary["peak_papers"] == 15

    def test_peak_year_tie_first_wins(self):
        """Test that first occurrence wins when multiple years tie for peak."""
        timeline = [
            {"year": "2020", "papers": 10, "citations": 20},
            {"year": "2021", "papers": 10, "citations": 25},
            {"year": "2022", "papers": 10, "citations": 30},
        ]
        
        summary = get_timeline_summary(timeline)
        
        # All years have 10 papers, first should win
        assert summary["peak_year"] == "2020"

    def test_year_range_extraction(self):
        """Test year range extraction from timeline."""
        timeline = [
            {"year": "2018", "papers": 5, "citations": 10},
            {"year": "2019", "papers": 8, "citations": 15},
            {"year": "2020", "papers": 12, "citations": 25},
        ]
        
        summary = get_timeline_summary(timeline)
        
        assert summary["year_range"] == ("2018", "2020")

    def test_missing_year_fields_handled(self):
        """Test that missing year fields are handled gracefully."""
        timeline = [
            {"papers": 10, "citations": 20},  # Missing year
            {"year": "2021", "papers": 15, "citations": 30},
        ]
        
        summary = get_timeline_summary(timeline)
        
        # Should still compute totals
        assert summary["total_papers"] == 25
        assert summary["total_citations"] == 50


# Made with Bob