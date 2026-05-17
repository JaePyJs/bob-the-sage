import asyncio
import streamlit as st
import time
import os

# --- Setup page config before anything else ---
st.set_page_config(
    page_title="SAGE: Research Engine",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Inject Streamlit secrets into environment variables for the backend
if hasattr(st, "secrets"):
    for k, v in st.secrets.items():
        os.environ[k] = str(v)

# --- Backend Imports ---
from backend.mcp_servers.semantic_scholar_mcp import search_papers, _generate_synthetic_citations
from backend.engines.citation_graph import build_citation_graph, get_graph_summary
from backend.engines.timeline import build_timeline, detect_paradigm_shifts
from backend.api.routes.synthesize import synthesize_literature, SynthesizePayload
from backend.api.routes.proposal import generate_proposal, ProposalPayload


def run_pipeline(query: str):
    """Run the entire SAGE backend pipeline synchronously for Streamlit."""
    with st.status(f"Running pipeline for '{query}'...", expanded=True) as status:
        try:
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
