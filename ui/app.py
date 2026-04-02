import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from graph.pipeline import graph

st.set_page_config(
    page_title="Agentic Research Paper Evaluator",
    page_icon="🔬",
    layout="wide",
)

st.title("🔬 Agentic Research Paper Evaluator")
st.caption("Powered by LangGraph + Groq (Llama 3.3 70B)")

arxiv_url = st.text_input(
    "arXiv URL",
    placeholder="https://arxiv.org/abs/1706.03762",
    label_visibility="visible",
)

run = st.button("▶ Evaluate Paper", type="primary", disabled=not arxiv_url.strip())

if run and arxiv_url.strip():
    progress_placeholder = st.empty()
    result = None

    with progress_placeholder.container():
        st.subheader("📊 Live Agent Progress")
        s_scraper      = st.status("Scraper — fetching paper...",     state="running")
        s_decomposer   = st.status("Decomposer — splitting sections...", state="running")
        s_consistency  = st.status("Consistency Agent",               state="running")
        s_grammar      = st.status("Grammar Agent",                   state="running")
        s_novelty      = st.status("Novelty Agent",                   state="running")
        s_fact         = st.status("Fact Checker Agent",              state="running")
        s_authenticity = st.status("Authenticity Agent",              state="running")

        # Stream the graph and update statuses as nodes complete
        state = {"arxiv_url": arxiv_url.strip(), "errors": []}
        for event in graph.stream(state, stream_mode="updates"):
            for node_name, node_output in event.items():
                if node_name == "scraper":
                    title = node_output.get("paper_title", "")
                    s_scraper.update(
                        label=f"Scraper — done ({len(node_output.get('raw_text',''))} chars)",
                        state="complete",
                    )
                elif node_name == "decomposer":
                    s_decomposer.update(label="Decomposer — sections extracted", state="complete")
                elif node_name == "consistency":
                    score = node_output.get("consistency_score", "?")
                    s_consistency.update(label=f"Consistency Agent — {score}/100", state="complete")
                elif node_name == "grammar":
                    rating = node_output.get("grammar_rating", "?")
                    s_grammar.update(label=f"Grammar Agent — {rating}", state="complete")
                elif node_name == "novelty":
                    idx = node_output.get("novelty_index", "?")
                    s_novelty.update(label=f"Novelty Agent — {idx}", state="complete")
                elif node_name == "fact_checker":
                    n = len(node_output.get("fact_check_log") or [])
                    s_fact.update(label=f"Fact Checker Agent — {n} claims checked", state="complete")
                elif node_name == "authenticity":
                    score = node_output.get("authenticity_score", "?")
                    s_authenticity.update(label=f"Authenticity Agent — {score:.1f}% risk", state="complete")
                elif node_name == "report_generator":
                    result = node_output

        # Collect final state by re-invoking (stream gives partial dicts per node)
        # Re-run is expensive; instead merge streamed outputs into final state
        # We already have everything from stream events above, so just invoke once more
        # Actually let's just do a full invoke to get the complete merged state

    # Clear progress and show results
    progress_placeholder.empty()

    # Run full invoke for complete merged state (stream above was for live updates)
    with st.spinner("Compiling final report..."):
        final = graph.invoke({"arxiv_url": arxiv_url.strip(), "errors": []})

    # --- Score cards ---
    st.subheader(f"📄 Judgement Report: {final.get('paper_title', '')}")
    st.caption(f"Authors: {final.get('paper_authors', '')}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Consistency Score", f"{final.get('consistency_score', 0)}/100")
    col2.metric("Grammar Rating", final.get("grammar_rating", "—"))
    col3.metric("Fabrication Risk", f"{final.get('authenticity_score', 0):.1f}%")

    col4, col5 = st.columns(2)
    col4.metric("Novelty Index", final.get("novelty_index", "—"))

    # Verdict badge
    consistency = final.get("consistency_score") or 0
    grammar = final.get("grammar_rating") or "Low"
    authenticity = final.get("authenticity_score") or 50.0
    if consistency >= 70 and grammar != "Low" and authenticity <= 30:
        verdict, color = "PASS", "green"
    elif consistency < 50 or authenticity > 70:
        verdict, color = "FAIL", "red"
    else:
        verdict, color = "CONDITIONAL PASS", "orange"

    col5.markdown(f"**Verdict:** :{color}[**{verdict}**]")

    # --- Full markdown report ---
    st.divider()
    st.markdown(final.get("report_markdown", ""))

    # --- PDF download ---
    pdf_path = final.get("report_pdf_path", "")
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="⬇ Download PDF Report",
                data=f.read(),
                file_name=os.path.basename(pdf_path),
                mime="application/pdf",
                type="primary",
            )

    # --- Errors ---
    errors = final.get("errors") or []
    non_fatal = [e for e in errors if "regex split" not in e]
    if non_fatal:
        with st.expander("⚠️ Non-fatal errors during evaluation"):
            for e in non_fatal:
                st.error(e)
