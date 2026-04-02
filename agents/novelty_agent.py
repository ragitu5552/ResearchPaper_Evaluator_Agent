import json
import re
from graph.state import PaperState
from utils.chunker import truncate_to_limit
from utils.llm_client import call_llm


def assess_novelty(state: PaperState) -> dict:
    """
    Assess the paper's uniqueness by evaluating its claimed novel contributions.
    Returns: {"novelty_index": str, "novelty_reasoning": str}
    """
    errors = []

    abstract = truncate_to_limit(state.get("abstract", ""), max_tokens=3000)
    methodology = state.get("methodology", "")
    methodology_excerpt = methodology[:2000] if methodology else ""

    if not abstract:
        errors.append("NoveltyAgent: abstract is empty.")
        return {"novelty_index": "Unclear", "novelty_reasoning": "No content to evaluate.", "errors": errors}

    prompt = f"""You are a research novelty evaluator.

ABSTRACT:
{abstract}

METHODOLOGY (first 2000 chars):
{methodology_excerpt}

Tasks:
1. Identify the paper's claimed novel contributions (quote them directly)
2. Evaluate how specific and differentiated these claims are
3. Note any red flags: vague novelty claims, missing comparisons to prior work, overclaiming

Respond in this exact JSON format:
{{
  "claimed_contributions": ["<contribution 1>", "<contribution 2>"],
  "novelty_index": "<Highly Novel | Moderately Novel | Incremental | Unclear>",
  "reasoning": "<3-4 sentences evaluating novelty>"
}}"""

    try:
        response = call_llm(prompt, temperature=0.2)
        response = re.sub(r'^```(?:json)?\s*|\s*```$', '', response.strip())
        data = json.loads(response)
        valid_indices = ("Highly Novel", "Moderately Novel", "Incremental", "Unclear")
        novelty_index = data.get("novelty_index", "Unclear")
        if novelty_index not in valid_indices:
            novelty_index = "Unclear"
        return {
            "novelty_index": novelty_index,
            "novelty_reasoning": data.get("reasoning", ""),
            "errors": errors,
        }
    except Exception as e:
        errors.append(f"NoveltyAgent failed: {e}")
        return {"novelty_index": "Unclear", "novelty_reasoning": "Evaluation failed.", "errors": errors}
