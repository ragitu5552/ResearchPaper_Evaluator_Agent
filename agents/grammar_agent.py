import json
import re
from graph.state import PaperState
from utils.chunker import truncate_to_limit
from utils.llm_client import call_llm


def check_grammar(state: PaperState) -> dict:
    """
    Evaluate professional tone and academic writing quality.
    Returns: {"grammar_rating": str, "grammar_reasoning": str}
    """
    errors = []

    abstract = truncate_to_limit(state.get("abstract", ""), max_tokens=3000)
    conclusion = truncate_to_limit(state.get("conclusion", "") or state.get("abstract", ""), max_tokens=3000)

    if not abstract and not conclusion:
        errors.append("GrammarAgent: insufficient content (abstract-only paper).")
        return {"grammar_rating": "Low", "grammar_reasoning": "Full paper text not available — HTML version not yet published on arXiv.", "errors": errors}

    prompt = f"""You are an academic writing expert evaluating a research paper's language quality.

ABSTRACT:
{abstract}

CONCLUSION:
{conclusion}

Evaluate the writing for: academic tone, clarity, grammar correctness,
professional vocabulary, sentence structure, and coherence.

Respond in this exact JSON format:
{{
  "rating": "<High|Medium|Low>",
  "reasoning": "<2-3 sentences explaining your rating>"
}}
High = publication-ready, Medium = needs minor revision, Low = needs significant revision."""

    try:
        response = call_llm(prompt, temperature=0.2)
        start, end = response.find('{'), response.rfind('}')
        data = json.loads(response[start:end + 1])
        rating = data.get("rating", "Medium")
        if rating not in ("High", "Medium", "Low"):
            rating = "Medium"
        return {
            "grammar_rating": rating,
            "grammar_reasoning": data.get("reasoning", ""),
            "errors": errors,
        }
    except Exception as e:
        errors.append(f"GrammarAgent failed: {e}")
        return {"grammar_rating": "Low", "grammar_reasoning": "Evaluation failed.", "errors": errors}
