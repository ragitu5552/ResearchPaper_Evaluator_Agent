import json
import re
from graph.state import PaperState
from utils.chunker import truncate_to_limit
from utils.llm_client import call_llm


def check_authenticity(state: PaperState) -> dict:
    """
    Calculate a Fabrication Probability score based on logical anomalies and red flags.
    Returns: {"authenticity_score": float, "authenticity_reasoning": str}
    """
    errors = []

    abstract = truncate_to_limit(state.get("abstract", ""), max_tokens=3000)
    results = truncate_to_limit(state.get("results", "") or state.get("abstract", ""), max_tokens=4000)

    if not abstract and not results:
        errors.append("AuthenticityAgent: insufficient content (abstract-only paper).")
        return {"authenticity_score": 50.0, "authenticity_reasoning": "Full paper text not available — HTML version not yet published on arXiv.", "errors": errors}

    prompt = f"""You are an AI integrity auditor. Evaluate this research paper for signs of
AI-generated content, fabricated results, or statistical anomalies.

ABSTRACT:
{abstract}

RESULTS:
{results}

Look for: suspiciously round numbers, impossible accuracy scores (e.g. 99.99%),
missing standard deviations, vague dataset descriptions, results that are too
clean, logical leaps without justification, generic placeholder-sounding language.

Respond in this exact JSON format:
{{
  "fabrication_probability": <float 0.0 to 100.0>,
  "reasoning": "<3-4 sentences explaining your assessment>",
  "red_flags": ["<flag 1>", "<flag 2>"]
}}
0.0 = very likely authentic, 100.0 = very likely fabricated/hallucinated."""

    try:
        response = call_llm(prompt, temperature=0.2)
        start, end = response.find('{'), response.rfind('}')
        data = json.loads(response[start:end + 1])
        score = float(data.get("fabrication_probability", 50.0))
        score = max(0.0, min(100.0, score))  # clamp to valid range
        reasoning = data.get("reasoning", "")
        red_flags = data.get("red_flags", [])
        # Attach red flags to reasoning for state storage
        if red_flags:
            reasoning += "\n\nRed Flags:\n" + "\n".join(f"- {f}" for f in red_flags)
        return {
            "authenticity_score": score,
            "authenticity_reasoning": reasoning,
            "errors": errors,
        }
    except Exception as e:
        errors.append(f"AuthenticityAgent failed: {e}")
        return {"authenticity_score": 50.0, "authenticity_reasoning": "Evaluation failed.", "errors": errors}
