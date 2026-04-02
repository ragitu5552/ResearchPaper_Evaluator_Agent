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
    conclusion = truncate_to_limit(state.get("conclusion", ""), max_tokens=3000)

    if not abstract and not conclusion:
        errors.append("GrammarAgent: abstract and conclusion are empty.")
        return {"grammar_rating": "Low", "grammar_reasoning": "No content to evaluate.", "errors": errors}

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
        response = re.sub(r'^```(?:json)?\s*|\s*```$', '', response.strip())
        data = json.loads(response)
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
