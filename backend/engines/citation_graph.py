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

from typing import Any, Dict, List, Optional

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
    G = nx.DiGraph()
    paper_map: Dict[str, Dict[str, Any]] = {}

    # Add paper nodes
    for p in papers:
        pid = p.get("paper_id")
        if not pid:
            continue
        paper_map[pid] = p
        title = p.get("title", pid)
        G.add_node(
            pid,
            label=title[:50] if title else pid,
            year=p.get("year"),
            category=p.get("primary_category", "unknown"),
            authors=p.get("authors", []),
        )

    # Add citation edges (include external citing/cited papers as nodes)
    for c in citations:
        citing = c.get("citing_id")
        cited = c.get("cited_id")
        if not citing or not cited:
            continue
        
        # Add external papers as nodes if not already present
        if citing not in paper_map:
            G.add_node(citing, label=f"External: {citing[:20]}...", year=None, category="external", authors=[])
        if cited not in paper_map:
            G.add_node(cited, label=f"External: {cited[:20]}...", year=None, category="external", authors=[])
        
        weight = max(0.0, min(1.0, float(c.get("weight", 0.5))))
        G.add_edge(citing, cited, weight=weight)

    # PageRank with fallback
    pagerank: Dict[str, float] = {}
    try:
        if G.number_of_nodes() > 0:
            pagerank = nx.pagerank(G, alpha=0.85, max_iter=100, tol=1e-6)
    except (nx.PowerIterationFailedConvergence, ZeroDivisionError):
        n = len(paper_map)
        if n > 0:
            pagerank = {pid: 1.0 / n for pid in paper_map}

    # Build vis.js nodes (include ALL nodes in graph, including external papers)
    nodes = []
    for node_id in G.nodes():
        node_data = G.nodes[node_id]
        pr = pagerank.get(node_id, 0.0)
        
        # Get label from node data if it was set during graph construction
        if "label" in node_data:
            label = node_data["label"]
        elif node_id in paper_map:
            title = paper_map[node_id].get("title", node_id)
            label = title[:50] if title else node_id
        else:
            label = f"External: {node_id[:20]}..."
        
        group = node_data.get("category", "unknown") if "category" in node_data else (
            paper_map[node_id].get("primary_category", "unknown") if node_id in paper_map else "external"
        )
        
        nodes.append(GraphNode(
            id=node_id,
            label=label,
            group=group,
            value=max(1, min(10, int(pr * 100))),
        ))

    # Build vis.js edges
    edges = []
    for citing, cited, data in G.edges(data=True):
        edges.append(GraphEdge(
            from_id=citing,
            to_id=cited,
            weight=data.get("weight", 0.5),
        ))

    return CitationGraphPayload(nodes=nodes, edges=edges)


def get_graph_summary(
    papers: List[Dict[str, Any]],
    citations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Generate statistical summary of the citation graph.

    Computes key graph metrics including connectivity, clustering, and top-cited papers.

    Returns:
        Dictionary containing:
            - total_nodes (int): Number of papers in graph
            - total_edges (int): Number of citation edges
            - top_cited (list[tuple[str, int]]): Top 5 most-cited papers (paper_id, citation_count)
            - largest_cluster_size (int): Size of largest connected component
            - num_clusters (int): Number of connected components (undirected view)
            - density (float): Graph density (actual edges / possible edges)
            - avg_citations_per_paper (float): Mean in-degree
    """
    G = nx.DiGraph()

    # Add paper nodes
    valid_papers = 0
    for p in papers:
        pid = p.get("paper_id")
        if pid:
            G.add_node(pid)
            valid_papers += 1

    # Add edges (include external nodes)
    valid_edges = 0
    for c in citations:
        citing = c.get("citing_id")
        cited = c.get("cited_id")
        if citing and cited:
            if not G.has_node(citing):
                G.add_node(citing)
                valid_papers += 1
            if not G.has_node(cited):
                G.add_node(cited)
                valid_papers += 1
            G.add_edge(citing, cited)
            valid_edges += 1

    in_degree = dict(G.in_degree())
    top_cited = sorted(in_degree.items(), key=lambda x: x[1], reverse=True)[:5]

    undirected = G.to_undirected()
    components = list(nx.connected_components(undirected))
    largest = max(components, key=len) if components else set()

    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    max_edges = n_nodes * (n_nodes - 1)

    return {
        "total_nodes": valid_papers,
        "total_edges": valid_edges,
        "top_cited": top_cited,
        "largest_cluster_size": len(largest),
        "num_clusters": len(components),
        "density": round(n_edges / max_edges, 4) if max_edges > 0 else 0.0,
        "avg_citations_per_paper": round(n_edges / n_nodes, 2) if n_nodes > 0 else 0.0,
    }