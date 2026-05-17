"""Citation graph engine — builds NetworkX graph from paper metadata + citation edges.

This module constructs directed citation graphs from academic paper metadata and citation
relationships, computes influence metrics using PageRank, and exports visualization-ready
data in vis.js format for frontend rendering.

Key Features:
- Directed graph construction with NetworkX
- PageRank-based influence scoring (alpha=0.85, standard academic setting)
- Robust error handling for disconnected graphs and edge cases
- vis.js compatible JSON export with scaled node sizes
- Graph summary statistics including clustering and top-cited papers

Performance Characteristics:
- Time Complexity: O(n + m) for graph construction, O(n*m) for PageRank
- Space Complexity: O(n + m) where n=nodes, m=edges
- Scales efficiently to 100-200 papers (typical query size)
- PageRank converges in ~100 iterations for academic citation graphs
"""

from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx

from backend.models.graph import CitationGraphPayload, GraphNode, GraphEdge


def build_citation_graph(
    papers: List[Dict[str, Any]],
    citations: List[Dict[str, Any]],
) -> CitationGraphPayload:
    """Build a citation graph from papers and citation edges.

    Constructs a directed graph where nodes represent papers and edges represent
    citations (citing_paper → cited_paper). Computes PageRank scores to identify
    influential papers and exports data in vis.js format for visualization.

    Args:
        papers: List of paper dictionaries containing:
            - paper_id (str, required): Unique identifier
            - title (str, optional): Paper title
            - year (int, optional): Publication year
            - primary_category (str, optional): Academic category/field
            - authors (list[str], optional): Author names
        citations: List of citation edge dictionaries containing:
            - citing_id (str, required): ID of paper making the citation
            - cited_id (str, required): ID of paper being cited
            - weight (float, optional): Edge weight (default: 0.5)

    Returns:
        CitationGraphPayload: Pydantic model containing:
            - nodes: List of GraphNode objects with id, label, group, and PageRank-scaled value
            - edges: List of GraphEdge objects with from_id, to_id, and weight

    Notes:
        - Only edges between papers in the input list are included (dangling citations ignored)
        - PageRank uses alpha=0.85 (standard damping factor for academic citations)
        - Node sizes scaled by PageRank: value = max(1, int(pagerank * 100))
        - Empty graphs return empty node/edge lists (no error)
        - Disconnected graphs handled gracefully with uniform fallback PageRank
    """
    # Initialize directed graph (citations flow from citing → cited)
    G = nx.DiGraph()

    # Build paper lookup map and add nodes with metadata
    paper_map: Dict[str, Dict[str, Any]] = {}
    for p in papers:
        pid = p.get("paper_id")
        if not pid:
            # Skip papers without IDs (data quality issue)
            continue
        
        paper_map[pid] = p
        
        # Add node with truncated label for visualization clarity
        title = p.get("title", pid)
        G.add_node(
            pid,
            label=title[:60] if title else pid,  # Truncate long titles
            year=p.get("year"),
            category=p.get("primary_category", "unknown"),
            authors=p.get("authors", []),
        )

    # Add citation edges (only between papers in our dataset)
    valid_edges = 0
    for c in citations:
        citing = c.get("citing_id")
        cited = c.get("cited_id")
        
        if not citing or not cited:
            # Skip malformed citation records
            continue
        
        # Only add edge if both papers exist in our dataset
        if citing in paper_map and cited in paper_map:
            weight = c.get("weight", 0.5)
            # Ensure weight is positive and reasonable
            weight = max(0.0, min(1.0, float(weight)))
            G.add_edge(citing, cited, weight=weight)
            valid_edges += 1

    # Compute PageRank for influence scoring
    # alpha=0.85: Standard damping factor (85% follow links, 15% random jump)
    # Handles disconnected graphs and converges for typical academic citation networks
    pagerank: Dict[str, float] = {}
    try:
        if G.number_of_nodes() > 0:
            pagerank = nx.pagerank(G, alpha=0.85, max_iter=100, tol=1e-6)
        else:
            # Empty graph case
            pagerank = {}
    except (nx.PowerIterationFailedConvergence, ZeroDivisionError):
        # Fallback: Uniform distribution if PageRank fails to converge
        # This can happen with certain graph structures (e.g., all disconnected nodes)
        num_nodes = len(paper_map)
        if num_nodes > 0:
            uniform_score = 1.0 / num_nodes
            pagerank = {pid: uniform_score for pid in paper_map}
        else:
            pagerank = {}

    # Build vis.js nodes with PageRank-scaled sizes
    nodes: List[GraphNode] = []
    for pid, p in paper_map.items():
        cat = p.get("primary_category", "unknown")
        pr_score = pagerank.get(pid, 0.0)
        
        # Scale PageRank to visual node size (1-10 range for vis.js)
        # Multiply by 100 to amplify differences, clamp to minimum of 1
        value = max(1, min(10, int(pr_score * 100)))
        
        # Truncate title for node label (50 chars for readability)
        title = p.get("title", pid)
        label = title[:50] if title else pid
        
        nodes.append(GraphNode(
            id=pid,
            label=label,
            group=cat,
            value=value,
        ))

    # Build vis.js edges (only include edges that were successfully added to graph)
    edges: List[GraphEdge] = []
    for c in citations:
        citing = c.get("citing_id")
        cited = c.get("cited_id")
        
        # Only export edges between papers in our dataset
        if citing in paper_map and cited in paper_map:
            weight = c.get("weight", 0.5)
            # Ensure weight is positive and reasonable (same clamping as graph construction)
            weight = max(0.0, min(1.0, float(weight)))
            edges.append(GraphEdge(
                from_id=citing,
                to_id=cited,
                weight=weight,
            ))

    return CitationGraphPayload(nodes=nodes, edges=edges)


def get_graph_summary(
    papers: List[Dict[str, Any]],
    citations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Generate statistical summary of the citation graph.

    Computes key graph metrics including connectivity, clustering, and top-cited papers.
    Useful for understanding graph structure and identifying influential papers.

    Args:
        papers: List of paper dictionaries (same format as build_citation_graph)
        citations: List of citation edge dictionaries (same format as build_citation_graph)

    Returns:
        Dictionary containing:
            - total_nodes (int): Number of papers in graph
            - total_edges (int): Number of citation edges
            - top_cited (list[tuple[str, int]]): Top 5 most-cited papers (paper_id, citation_count)
            - largest_cluster_size (int): Size of largest connected component
            - num_clusters (int): Number of connected components (undirected view)
            - density (float): Graph density (actual edges / possible edges)
            - avg_citations_per_paper (float): Mean in-degree

    Notes:
        - Clustering analysis uses undirected view (citations as bidirectional connections)
        - Empty graphs return zeros for all metrics
        - Top-cited list may be shorter than 5 if fewer papers exist
    """
    # Build directed graph
    G = nx.DiGraph()
    
    # Add nodes (with validation)
    valid_papers = 0
    for p in papers:
        pid = p.get("paper_id")
        if pid:
            G.add_node(pid)
            valid_papers += 1
    
    # Add edges (only between valid nodes)
    valid_edges = 0
    for c in citations:
        citing = c.get("citing_id")
        cited = c.get("cited_id")
        if citing and cited and G.has_node(citing) and G.has_node(cited):
            G.add_edge(citing, cited)
            valid_edges += 1

    # Compute in-degree (citation counts)
    in_degree: Dict[str, int] = dict(G.in_degree())  # type: ignore[arg-type]
    
    # Find top 5 most-cited papers
    top_cited = sorted(in_degree.items(), key=lambda x: x[1], reverse=True)[:5]

    # Analyze clustering using undirected view
    # (treat citations as bidirectional connections for community detection)
    undirected = G.to_undirected()
    components = list(nx.connected_components(undirected))
    largest_cluster = max(components, key=len) if components else set()

    # Compute graph density (actual edges / possible edges)
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    max_possible_edges = num_nodes * (num_nodes - 1)  # Directed graph
    density = num_edges / max_possible_edges if max_possible_edges > 0 else 0.0

    # Compute average citations per paper
    avg_citations = num_edges / num_nodes if num_nodes > 0 else 0.0

    return {
        "total_nodes": valid_papers,
        "total_edges": valid_edges,
        "top_cited": top_cited,
        "largest_cluster_size": len(largest_cluster),
        "num_clusters": len(components),
        "density": round(density, 4),
        "avg_citations_per_paper": round(avg_citations, 2),
    }

# Made with Bob
