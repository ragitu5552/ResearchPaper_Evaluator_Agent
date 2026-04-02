import json
import re
from graph.state import PaperState
from utils.chunker import truncate_to_limit
from utils.llm_client import call_llm

COMBINED_LIMIT = 12000  # tokens for methodology + results together


def check_consistency(state: PaperState) -> dict:
    """
    Check if the methodology actually supports the claimed results.
    Returns: {"consistency_score": int, "consistency_reasoning": str}
    """
    errors = []

    methodology = state.get("methodology", "")
    results = state.get("results", "")

    if not methodology and not results:
        errors.append("ConsistencyAgent: both methodology and results are empty.")
        return {"consistency_score": 0, "consistency_reasoning": "No content to evaluate.", "errors": errors}

    # Truncate combined content to 12k tokens
    half = COMBINED_LIMIT // 2
    methodology = truncate_to_limit(methodology, max_tokens=half)
    results = truncate_to_limit(results, max_tokens=half)

    prompt = f"""You are a peer reviewer checking internal consistency of a research paper.

METHODOLOGY SECTION:
{methodology}

RESULTS SECTION:
{results}

Evaluate: Does the described methodology logically support the claimed results?
Look for: missing experimental steps, overclaimed results, statistical gaps, logical leaps.

Respond in this exact JSON format:
{{
  "score": <integer 0-100>,
  "reasoning": "<2-3 sentences explaining the score>"
}}
Score guide: 90-100=fully supported, 70-89=mostly supported with minor gaps,
50-69=partially supported, 30-49=significant gaps, 0-29=methodology does not support results."""

    try:
        response = call_llm(prompt, temperature=0.2)
        response = re.sub(r'^```(?:json)?\s*|\s*```$', '', response.strip())
        data = json.loads(response)
        return {
            "consistency_score": int(data.get("score", 0)),
            "consistency_reasoning": data.get("reasoning", ""),
            "errors": errors,
        }
    except Exception as e:
        errors.append(f"ConsistencyAgent failed: {e}")
        return {"consistency_score": 0, "consistency_reasoning": "Evaluation failed.", "errors": errors}
