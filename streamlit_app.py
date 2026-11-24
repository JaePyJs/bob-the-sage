import asyncio
import json
import os
from pathlib import Path

import streamlit as st

from backend.engines.citation_graph import build_citation_graph, get_graph_summary
from backend.engines.timeline import build_timeline, detect_paradigm_shifts

# --- Setup page config before anything else ---
st.set_page_config(
    page_title="SAGE: Research Engine",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

WORKED_EXAMPLE_PATH = Path(__file__).with_name("examples") / "attention_citations.json"


def show_worked_example():
    example = json.loads(WORKED_EXAMPLE_PATH.read_text(encoding="utf-8"))
    papers = example["papers"]
    citations = example["citations"]
    papers_by_id = {paper["paper_id"]: paper for paper in papers}

    graph = build_citation_graph(papers, citations)
    timeline = build_timeline(papers, citations)

    st.header(example["query"])
    st.write(
        "Explore a hand-picked set of papers and follow each citation back to the original reference. "
        "SAGE builds this graph and timeline locally, without API keys."
    )
    paper_count, citation_count = st.columns(2)
    paper_count.metric("Papers", len(graph.nodes))
    citation_count.metric("Checked citations", len(graph.edges))

    graph_tab, timeline_tab, source_tab = st.tabs(["Citation graph", "Timeline", "Sources"])
    with graph_tab:
        st.caption("Arrows point from the paper making the citation to the paper it cites.")
        dot = ['digraph { rankdir=BT; bgcolor="white"; node [shape=box, style=rounded];']
        for node in graph.nodes:
            label = papers_by_id[node.id]["short_title"]
            dot.append(f"{json.dumps(node.id)} [label={json.dumps(label)}];")
        for edge in graph.edges:
            dot.append(f"{json.dumps(edge.from_id)} -> {json.dumps(edge.to_id)};")
        st.graphviz_chart("\n".join([*dot, "}"]))

    with timeline_tab:
        st.caption("Citations count toward the publication year of the paper receiving them.")
        st.table(
            [
                {"Year": row["year"], "Papers": row["papers"], "Citations received": row["citations"]}
                for row in timeline
            ]
        )

    with source_tab:
        st.subheader("Papers")
        for paper in papers:
            st.markdown(f"- [{paper['title']}]({paper['url']}) ({paper['year']}, {paper['venue']})")

        st.subheader("Where to check each citation")
        for citation in citations:
            citing = papers_by_id[citation["citing_id"]]["short_title"]
            cited = papers_by_id[citation["cited_id"]]["short_title"]
            st.markdown(f"- {citing} cites {cited}. [{citation['reference']}]({citation['reference_url']})")

    st.caption(
        "Counts apply only to these four selected papers and their in-sample references. "
        "Empty years reflect the sample. This example runs without live search or AI synthesis."
    )


def run_pipeline(query: str):
    """Run the entire SAGE backend pipeline synchronously for Streamlit."""
    with st.status(f"Running pipeline for '{query}'...", expanded=True) as status:
        try:
            try:
                for key, value in st.secrets.items():
                    os.environ[key] = str(value)
            except FileNotFoundError:
                pass

            from backend.api.routes.proposal import generate_proposal, ProposalPayload
            from backend.api.routes.synthesize import synthesize_literature, SynthesizePayload
            from backend.mcp_servers.semantic_scholar_mcp import search_papers, _generate_synthetic_citations

            st.write("🔍 Searching academic databases...")
            # We use asyncio to run the async API
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Step 1: Discovery
            search_result = loop.run_until_complete(search_papers(query, max_results=30, categories=[]))
            papers = search_result["papers"]
            citations = search_result["citations"]
            
            if not papers:
                status.update(label="No papers found.", state="error")
                return None
            
            st.write(f"✅ Found {len(papers)} papers.")

            # Step 2: Graph & Timeline
            st.write("📊 Building citation network & timeline...")
            if not citations and papers:
                citations = _generate_synthetic_citations(papers)
                
            graph = build_citation_graph(papers, citations)
            graph_summary = get_graph_summary(papers, citations)
            timeline = build_timeline(papers, citations)
            shifts = detect_paradigm_shifts(timeline)
            
            st.write("🧠 Synthesizing literature using Gemini...")
            synth_payload = SynthesizePayload(query=query, papers=papers, output_language="en")
            synthesis_data = loop.run_until_complete(synthesize_literature(synth_payload))

            st.write("📝 Generating research proposal draft...")
            prop_payload = ProposalPayload(
                query=query, 
                papers=papers, 
                paradigm_shifts=shifts, 
                graph_summary=graph_summary, 
                timeline=timeline, 
                output_language="en"
            )
            proposal_latex = loop.run_until_complete(generate_proposal(prop_payload))
            
            status.update(label="Pipeline Complete!", state="complete", expanded=False)
            
            return {
                "papers": papers,
                "graph_summary": graph_summary,
                "timeline": timeline,
                "shifts": shifts,
                "synthesis": synthesis_data,
                "proposal": proposal_latex
            }
        except Exception as e:
            status.update(label=f"Pipeline Error: {e}", state="error")
            return None


def main():
    st.title("SAGE: Systematic Academic Guidance Engine")
    mode = st.radio("Analysis mode", ["Worked example", "Live search"], horizontal=True)
    if mode == "Worked example":
        show_worked_example()
        return

    st.markdown("Enter a query to discover, analyze, and synthesize academic research across multiple disciplines.")

    query = st.text_input("Research Topic", placeholder="e.g., Quantum computing error correction...")
    
    if st.button("Run Pipeline", type="primary"):
        if not query.strip():
            st.warning("Please enter a research topic.")
            return
            
        results = run_pipeline(query)
        
        if results:
            st.success("Pipeline executed successfully!")
            
            tab1, tab2, tab3, tab4 = st.tabs(["📚 AI Review", "🕸️ Citation Graph", "📈 Timeline", "📝 Proposal"])
            
            with tab1:
                st.subheader("Executive Summary")
                synthesis = results["synthesis"]
                st.write(synthesis.get("executive_summary", "No summary available."))
                
                st.subheader("Key Themes")
                for theme in synthesis.get("key_themes", []):
                    st.markdown(f"**{theme.get('name', 'Theme')}**")
                    st.write(theme.get('description', ''))
                    
                st.subheader("Research Gaps")
                for gap in synthesis.get("research_gaps", []):
                    st.error(f"**Gap:** {gap.get('gap')}\n\n**Impact:** {gap.get('impact')}")
                    
                st.divider()
                st.subheader("📚 Source Papers (Legitimacy Verification)")
                st.markdown("All AI synthesis above is grounded in the following real, peer-reviewed academic papers:")
                
                for i, p in enumerate(results.get("papers", [])):
                    pid = p.get('paper_id', '')
                    # Semantic Scholar IDs are 40-character hex hashes, arXiv IDs are shorter (e.g., 2305.12345)
                    url = f"https://semanticscholar.org/paper/{pid}" if len(str(pid)) == 40 else f"https://arxiv.org/abs/{pid}"
                    
                    authors = ", ".join(p.get("authors", [])[:3])
                    if len(p.get("authors", [])) > 3: 
                        authors += " et al."
                        
                    st.markdown(f"{i+1}. **[{p.get('title', 'Untitled')}]({url})** ({p.get('year', 'N/A')}) — *{authors}*")

            with tab2:
                st.subheader("Network Metrics")
                metrics = results["graph_summary"]
                col1, col2, col3 = st.columns(3)
                col1.metric("Nodes (Papers)", metrics.get("total_nodes", 0))
                col2.metric("Edges (Citations)", metrics.get("total_edges", 0))
                col3.metric("Clusters Identified", metrics.get("num_clusters", 0))
                
                st.info("The interactive network visualization is optimized for the Next.js UI. Metrics are shown here for deployment preview.")

            with tab3:
                st.subheader("Publication Velocity & Shifts")
                timeline = results["timeline"]
                shifts = results["shifts"]
                
                if timeline:
                    years = [t["year"] for t in timeline]
                    counts = [t["papers"] for t in timeline]
                    chart_data = {
                        "Year": years,
                        "Publications": counts
                    }
                    st.bar_chart(chart_data, x="Year", y="Publications")
                    
                    if shifts:
                        st.subheader("Paradigm Shifts Detected")
                        for shift in shifts:
                            st.warning(f"**{shift['year']}**: {shift['growth']}% Growth")
                else:
                    st.write("Not enough temporal data.")

            with tab4:
                st.subheader("Generated LaTeX Proposal")
                proposal = results["proposal"]
                st.code(proposal.get("latex", "") if isinstance(proposal, dict) else proposal, language="latex")
                st.download_button("Download .tex", data=proposal.get("latex", "") if isinstance(proposal, dict) else proposal, file_name="sage_proposal.tex")

if __name__ == "__main__":
    main()
