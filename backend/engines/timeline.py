"""Timeline engine — computes yearly publication and citation trends.

This module analyzes temporal patterns in academic literature by aggregating papers
and citations by year, detecting paradigm shifts through growth rate analysis, and
providing statistical summaries of research activity over time.

Key Features:
- Year-by-year aggregation of papers and citations
- Gap filling for continuous timeline visualization
- Paradigm shift detection (>100% year-over-year growth)
- Robust handling of sparse data and edge cases
- Statistical validation of growth patterns

Performance Characteristics:
- Time Complexity: O(n + m) where n=papers, m=citations
- Space Complexity: O(y) where y=unique years in dataset
- Efficient for typical academic datasets (decades of data)
"""

from typing import Any, Dict, List, Optional, Tuple


def build_timeline(
    papers: List[Dict[str, Any]],
    citations: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Build timeline data from papers and citations.

    Aggregates papers and citations by publication year, creating a continuous
    timeline from the earliest to latest year in the dataset. Missing years are
    filled with zero counts for visualization continuity.

    Args:
        papers: List of paper dictionaries containing:
            - paper_id (str, required): Unique identifier
            - year (int, optional): Publication year
        citations: List of citation edge dictionaries containing:
            - citing_id (str, required): ID of citing paper
            - cited_id (str, required): ID of cited paper

    Returns:
        List of timeline dictionaries, sorted by year, each containing:
            - year (str): Year as string for JSON serialization
            - papers (int): Number of papers published in that year
            - citations (int): Number of citations to papers from that year

    Notes:
        - Papers without year metadata are excluded from timeline
        - Citations are attributed to the cited paper's publication year
        - Timeline includes all years from min to max, filling gaps with zeros
        - Empty input returns empty list (no error)
        - Years are returned as strings for consistent JSON serialization

    Example:
        >>> papers = [
        ...     {"paper_id": "p1", "year": 2020},
        ...     {"paper_id": "p2", "year": 2022}
        ... ]
        >>> citations = [{"citing_id": "p2", "cited_id": "p1"}]
        >>> build_timeline(papers, citations)
        [
            {"year": "2020", "papers": 1, "citations": 1},
            {"year": "2021", "papers": 0, "citations": 0},
            {"year": "2022", "papers": 1, "citations": 0}
        ]
    """
    # Count papers per year (only papers with valid year metadata)
    paper_years: Dict[int, int] = {}
    for p in papers:
        year = p.get("year")
        if year is not None and isinstance(year, int):
            # Validate year is reasonable (1900-2100 range)
            if 1900 <= year <= 2100:
                paper_years[year] = paper_years.get(year, 0) + 1

    # Build paper_id -> year mapping for citation attribution
    paper_year_map: Dict[str, int] = {}
    for p in papers:
        pid = p.get("paper_id")
        year = p.get("year")
        if pid and year is not None and isinstance(year, int):
            if 1900 <= year <= 2100:
                paper_year_map[pid] = year

    # Count citations per year (attributed to cited paper's publication year)
    # This shows which years' papers are being cited, indicating influence
    citation_years: Dict[int, int] = {}
    for c in citations:
        cited_id = c.get("cited_id")
        if cited_id and cited_id in paper_year_map:
            cited_year = paper_year_map[cited_id]
            citation_years[cited_year] = citation_years.get(cited_year, 0) + 1

    # Determine year range for timeline
    all_years = sorted(set(list(paper_years.keys()) + list(citation_years.keys())))
    
    if not all_years:
        # No valid years found - return empty timeline
        return []

    # Fill gaps in timeline for continuous visualization
    min_year = min(all_years)
    max_year = max(all_years)
    
    timeline: List[Dict[str, Any]] = []
    for year in range(min_year, max_year + 1):
        timeline.append({
            "year": str(year),  # String for JSON serialization
            "papers": paper_years.get(year, 0),
            "citations": citation_years.get(year, 0),
        })

    return timeline


def detect_paradigm_shifts(
    timeline: List[Dict[str, Any]],
    growth_threshold: float = 2.0,
    min_baseline: int = 2,
) -> List[Dict[str, Any]]:
    """Detect paradigm shifts in research activity.

    Identifies years with significant growth in publication volume, indicating
    potential paradigm shifts, breakthrough discoveries, or emerging research areas.
    Uses year-over-year growth rate analysis with configurable thresholds.

    Args:
        timeline: List of timeline dictionaries from build_timeline(), each containing:
            - year (str): Year identifier
            - papers (int): Paper count for that year
            - citations (int): Citation count for that year
        growth_threshold: Minimum growth multiplier to qualify as shift (default: 2.0 = 100% growth)
        min_baseline: Minimum papers in previous year to consider (default: 2, avoids noise from sparse data)

    Returns:
        List of paradigm shift dictionaries, each containing:
            - year (str): Year when shift occurred
            - growth (int): Growth percentage (e.g., 150 for 150% growth)
            - prev_count (int): Paper count in previous year
            - curr_count (int): Paper count in shift year

    Notes:
        - Only considers consecutive years (no gap handling)
        - Requires previous year to have >= min_baseline papers (avoids false positives from sparse data)
        - Growth calculated as: (curr_count / prev_count - 1) * 100
        - Empty timeline or single-year timeline returns empty list
        - Sorted by year (chronological order)

    Statistical Rationale:
        - 100% growth threshold (2.0x) is standard for detecting significant shifts
        - min_baseline=2 filters noise from early/sparse years (1→3 papers not meaningful)
        - Year-over-year comparison captures sudden changes vs. gradual trends

    Example:
        >>> timeline = [
        ...     {"year": "2020", "papers": 5, "citations": 10},
        ...     {"year": "2021", "papers": 12, "citations": 25}
        ... ]
        >>> detect_paradigm_shifts(timeline)
        [{"year": "2021", "growth": 140, "prev_count": 5, "curr_count": 12}]
    """
    shifts: List[Dict[str, Any]] = []
    
    # Need at least 2 years for year-over-year comparison
    if len(timeline) < 2:
        return shifts

    # Analyze consecutive year pairs
    for i in range(1, len(timeline)):
        prev = timeline[i - 1]
        curr = timeline[i]
        
        prev_count = prev.get("papers", 0)
        curr_count = curr.get("papers", 0)
        
        # Validate data types (defensive programming)
        if not isinstance(prev_count, (int, float)) or not isinstance(curr_count, (int, float)):
            continue
        
        # Apply minimum baseline filter to avoid false positives from sparse data
        # Example: 1→3 papers (200% growth) is noise, not a paradigm shift
        if prev_count < min_baseline:
            continue
        
        # Prevent division by zero (should be caught by min_baseline, but defensive)
        if prev_count <= 0:
            continue
        
        # Calculate growth multiplier
        growth_multiplier = curr_count / prev_count
        
        # Check if growth exceeds threshold
        if growth_multiplier >= growth_threshold:
            # Calculate growth percentage for reporting
            growth_pct = round((growth_multiplier - 1.0) * 100)
            
            shifts.append({
                "year": curr.get("year", "unknown"),
                "growth": growth_pct,
                "prev_count": int(prev_count),
                "curr_count": int(curr_count),
            })

    return shifts


def get_timeline_summary(
    timeline: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Generate statistical summary of timeline data.

    Computes aggregate statistics and trends across the entire timeline,
    providing insights into research activity patterns and growth trajectories.

    Args:
        timeline: List of timeline dictionaries from build_timeline()

    Returns:
        Dictionary containing:
            - total_papers (int): Total papers across all years
            - total_citations (int): Total citations across all years
            - year_range (tuple[str, str] | None): (min_year, max_year) or None if empty
            - avg_papers_per_year (float): Mean papers per year
            - avg_citations_per_year (float): Mean citations per year
            - peak_year (str | None): Year with most papers
            - peak_papers (int): Paper count in peak year
            - growth_rate (float | None): Overall CAGR (Compound Annual Growth Rate) or None

    Notes:
        - Empty timeline returns zeros/None for all metrics
        - CAGR calculated only if timeline spans multiple years with non-zero start
        - All averages rounded to 2 decimal places
        - Peak year is first occurrence if multiple years tie

    Example:
        >>> timeline = [
        ...     {"year": "2020", "papers": 5, "citations": 10},
        ...     {"year": "2021", "papers": 10, "citations": 25}
        ... ]
        >>> get_timeline_summary(timeline)
        {
            "total_papers": 15,
            "total_citations": 35,
            "year_range": ("2020", "2021"),
            "avg_papers_per_year": 7.5,
            "avg_citations_per_year": 17.5,
            "peak_year": "2021",
            "peak_papers": 10,
            "growth_rate": 100.0
        }
    """
    if not timeline:
        return {
            "total_papers": 0,
            "total_citations": 0,
            "year_range": None,
            "avg_papers_per_year": 0.0,
            "avg_citations_per_year": 0.0,
            "peak_year": None,
            "peak_papers": 0,
            "growth_rate": None,
        }

    # Aggregate totals
    total_papers = sum(t.get("papers", 0) for t in timeline)
    total_citations = sum(t.get("citations", 0) for t in timeline)
    
    # Year range
    years = [t.get("year") for t in timeline if t.get("year")]
    year_range = (years[0], years[-1]) if years else None
    
    # Averages
    num_years = len(timeline)
    avg_papers = total_papers / num_years if num_years > 0 else 0.0
    avg_citations = total_citations / num_years if num_years > 0 else 0.0
    
    # Peak year
    peak_entry = max(timeline, key=lambda t: t.get("papers", 0))
    peak_year = peak_entry.get("year")
    peak_papers = peak_entry.get("papers", 0)
    
    # Calculate CAGR (Compound Annual Growth Rate)
    # CAGR = (ending_value / beginning_value)^(1/years) - 1
    growth_rate: Optional[float] = None
    if num_years > 1:
        first_count = timeline[0].get("papers", 0)
        last_count = timeline[-1].get("papers", 0)
        
        if first_count > 0 and last_count > 0:
            years_elapsed = num_years - 1
            calculated_rate = (pow(last_count / first_count, 1.0 / years_elapsed) - 1.0) * 100
            growth_rate = round(calculated_rate, 2)
    
    return {
        "total_papers": total_papers,
        "total_citations": total_citations,
        "year_range": year_range,
        "avg_papers_per_year": round(avg_papers, 2),
        "avg_citations_per_year": round(avg_citations, 2),
        "peak_year": peak_year,
        "peak_papers": peak_papers,
        "growth_rate": growth_rate,
    }

# Made with Bob
