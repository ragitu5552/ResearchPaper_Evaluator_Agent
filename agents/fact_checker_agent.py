import json
import re
from graph.state import PaperState
from utils.chunker import truncate_to_limit
from utils.llm_client import call_llm


def check_facts(state: PaperState) -> dict:
    """
    Extract specific verifiable claims and flag which are standard vs suspicious.
    Returns: {"fact_check_log": list}
    """
    errors = []

    # Use abstract + results as the fact-rich sections
    abstract = state.get("abstract", "")
    results = state.get("results", "")
    combined = f"{abstract}\n\n{results}"
    text_excerpt = truncate_to_limit(combined, max_tokens=6000)

    if not text_excerpt.strip():
        errors.append("FactCheckerAgent: no text content available.")
        return {"fact_check_log": [], "errors": errors}

    prompt = f"""You are a fact-checker for a research paper.

FULL TEXT EXCERPT:
{text_excerpt}

Extract up to 8 specific factual claims: numerical constants, cited statistics,
named datasets with stated sizes, mathematical formulas, benchmark scores, or
historical facts. For each, assess if it appears standard/verifiable.

Respond in this exact JSON format:
{{
  "fact_check_log": [
    {{
      "claim": "<the exact claim from the paper>",
      "status": "<verified|unverified|suspicious>",
      "note": "<brief explanation>"
    }}
  ]
}}"""

    try:
        response = call_llm(prompt, temperature=0.1)
        response = re.sub(r'^```(?:json)?\s*|\s*```$', '', response.strip())
        data = json.loads(response)
        log = data.get("fact_check_log", [])
        # Normalize status values
        valid_statuses = {"verified", "unverified", "suspicious"}
        for item in log:
            if item.get("status") not in valid_statuses:
                item["status"] = "unverified"
        return {"fact_check_log": log, "errors": errors}
    except Exception as e:
        errors.append(f"FactCheckerAgent failed: {e}")
        return {"fact_check_log": [], "errors": errors}
