from langgraph.graph import StateGraph, END, START
from graph.state import PaperState
from agents.scraper import scrape_paper
from agents.decomposer import decompose_paper
from agents.consistency_agent import check_consistency
from agents.grammar_agent import check_grammar
from agents.novelty_agent import assess_novelty
from agents.fact_checker_agent import check_facts
from agents.authenticity_agent import check_authenticity
from report.generator import generate_report
from report.pdf_exporter import export_pdf


# --- Node wrappers ---

def scraper_node(state: PaperState) -> dict:
    return scrape_paper(state)


def decomposer_node(state: PaperState) -> dict:
    return decompose_paper(state)


def consistency_node(state: PaperState) -> dict:
    return check_consistency(state)


def grammar_node(state: PaperState) -> dict:
    return check_grammar(state)


def novelty_node(state: PaperState) -> dict:
    return assess_novelty(state)


def fact_checker_node(state: PaperState) -> dict:
    return check_facts(state)


def authenticity_node(state: PaperState) -> dict:
    return check_authenticity(state)


def aggregator_node(state: PaperState) -> dict:
    """Validate all agent outputs are present; fill defaults for any that failed."""
    errors = []
    updates = {}

    if state.get("consistency_score") is None:
        errors.append("Aggregator: consistency_score missing, defaulting to 0.")
        updates["consistency_score"] = 0
        updates["consistency_reasoning"] = "Agent did not produce output."

    if state.get("grammar_rating") is None:
        errors.append("Aggregator: grammar_rating missing, defaulting to Low.")
        updates["grammar_rating"] = "Low"
        updates["grammar_reasoning"] = "Agent did not produce output."

    if state.get("novelty_index") is None:
        errors.append("Aggregator: novelty_index missing, defaulting to Unclear.")
        updates["novelty_index"] = "Unclear"
        updates["novelty_reasoning"] = "Agent did not produce output."

    if state.get("fact_check_log") is None:
        errors.append("Aggregator: fact_check_log missing, defaulting to empty.")
        updates["fact_check_log"] = []

    if state.get("authenticity_score") is None:
        errors.append("Aggregator: authenticity_score missing, defaulting to 50.")
        updates["authenticity_score"] = 50.0
        updates["authenticity_reasoning"] = "Agent did not produce output."

    updates["errors"] = errors
    return updates


def report_generator_node(state: PaperState) -> dict:
    """Generate markdown report and export to PDF."""
    errors = list(state.get("errors", []))

    try:
        markdown = generate_report(state)
    except Exception as e:
        errors.append(f"ReportGenerator: markdown generation failed: {e}")
        markdown = f"# Report Generation Failed\n\nError: {e}"

    try:
        pdf_path = export_pdf(markdown, state.get("paper_title", "report"))
    except Exception as e:
        errors.append(f"PDFExporter: export failed: {e}")
        pdf_path = ""

    return {
        "report_markdown": markdown,
        "report_pdf_path": pdf_path,
        "errors": errors,
    }


# --- Graph builder ---

def build_graph():
    builder = StateGraph(PaperState)

    builder.add_node("scraper", scraper_node)
    builder.add_node("decomposer", decomposer_node)
    builder.add_node("consistency", consistency_node)
    builder.add_node("grammar", grammar_node)
    builder.add_node("novelty", novelty_node)
    builder.add_node("fact_checker", fact_checker_node)
    builder.add_node("authenticity", authenticity_node)
    builder.add_node("aggregator", aggregator_node)
    builder.add_node("report_generator", report_generator_node)

    # Linear: START → scraper → decomposer
    builder.add_edge(START, "scraper")
    builder.add_edge("scraper", "decomposer")

    # Fan-out: decomposer → all 5 agents in parallel
    builder.add_conditional_edges(
        "decomposer",
        lambda state: ["consistency", "grammar", "novelty", "fact_checker", "authenticity"],
        ["consistency", "grammar", "novelty", "fact_checker", "authenticity"],
    )

    # Fan-in: all 5 agents → aggregator
    for agent in ["consistency", "grammar", "novelty", "fact_checker", "authenticity"]:
        builder.add_edge(agent, "aggregator")

    builder.add_edge("aggregator", "report_generator")
    builder.add_edge("report_generator", END)

    return builder.compile()


# Singleton graph instance
graph = build_graph()
