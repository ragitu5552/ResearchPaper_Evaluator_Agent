import re
import json
from graph.state import PaperState
from utils.chunker import truncate_to_limit
from utils.llm_client import call_llm

SECTION_PATTERNS = {
    "abstract": re.compile(r'^(abstract)\s*$', re.IGNORECASE),
    "methodology": re.compile(r'^(\d[\.\d]*\s*)?(method(?:ology)?|approach|proposed\s+method|model|system\s+design)\s*$', re.IGNORECASE),
    "results": re.compile(r'^(\d[\.\d]*\s*)?(results?|experiments?|evaluation|performance|findings)\s*$', re.IGNORECASE),
    "conclusion": re.compile(r'^(\d[\.\d]*\s*)?(conclusion|concluding\s+remarks?|summary)\s*$', re.IGNORECASE),
}

MIN_SECTION_CHARS = 500  # sections shorter than this are considered failed


def _regex_split(text: str) -> dict:
    """Try to split text into sections using regex on section headers."""
    lines = text.split('\n')
    section_positions = {}

    for i, line in enumerate(lines):
        stripped = line.strip()
        if len(stripped) < 3 or len(stripped) > 80:
            continue
        for section, pattern in SECTION_PATTERNS.items():
            if pattern.match(stripped) and section not in section_positions:
                section_positions[section] = i

    if len(section_positions) < 2:
        return {}

    sorted_sections = sorted(section_positions.items(), key=lambda x: x[1])
    result = {}
    for idx, (section_name, start_line) in enumerate(sorted_sections):
        end_line = sorted_sections[idx + 1][1] if idx + 1 < len(sorted_sections) else len(lines)
        result[section_name] = '\n'.join(lines[start_line:end_line]).strip()

    return result


def _sections_are_valid(sections: dict) -> bool:
    """Return True only if ALL 4 sections have meaningful content."""
    required = ("abstract", "methodology", "results", "conclusion")
    return all(len(sections.get(k, "")) >= MIN_SECTION_CHARS for k in required)


def _llm_split(text: str) -> dict:
    """Use LLM to extract sections when regex fails or yields thin results."""
    excerpt = truncate_to_limit(text, max_tokens=10000)
    prompt = f"""You are given a research paper. Extract exactly these four sections:
1. abstract
2. methodology  (Methods / Approach / Model — the section describing HOW the work was done)
3. results      (Experiments / Evaluation / Results — the section with numbers and findings)
4. conclusion   (Conclusion / Summary / Future Work)

Return ONLY a valid JSON object with keys: "abstract", "methodology", "results", "conclusion".
Each value must contain the actual section text (not just the heading).
If a section is missing, use an empty string.

PAPER TEXT:
{excerpt}

Respond with valid JSON only. No markdown fences."""

    try:
        response = call_llm(prompt, temperature=0.1)
        response = re.sub(r'^```(?:json)?\s*|\s*```$', '', response.strip())
        return json.loads(response)
    except Exception:
        return {}


def decompose_paper(state: PaperState) -> dict:
    """
    Split raw_text into 4 sections: abstract, methodology, results, conclusion.
    Returns: {"abstract": str, "methodology": str, "results": str, "conclusion": str, "full_sections": dict}
    """
    errors = []
    raw_text = state.get("raw_text", "")

    if not raw_text:
        errors.append("Decomposer: raw_text is empty, cannot decompose.")
        empty = {"abstract": "", "methodology": "", "results": "", "conclusion": ""}
        return {**empty, "full_sections": empty, "errors": errors}

    # Try regex first
    sections = _regex_split(raw_text)

    # Fall back to LLM if regex didn't produce valid sections
    if not _sections_are_valid(sections):
        errors.append("Decomposer: regex split insufficient, using LLM fallback.")
        sections = _llm_split(raw_text)

    # Truncate each section to token limit before storing
    abstract = truncate_to_limit(sections.get("abstract", ""), max_tokens=15000)
    methodology = truncate_to_limit(sections.get("methodology", ""), max_tokens=15000)
    results = truncate_to_limit(sections.get("results", ""), max_tokens=15000)
    conclusion = truncate_to_limit(sections.get("conclusion", ""), max_tokens=15000)

    for name, val in [("abstract", abstract), ("methodology", methodology),
                      ("results", results), ("conclusion", conclusion)]:
        if not val:
            errors.append(f"Decomposer: could not extract '{name}' section.")

    full_sections = {
        "abstract": abstract,
        "methodology": methodology,
        "results": results,
        "conclusion": conclusion,
    }

    return {
        "abstract": abstract,
        "methodology": methodology,
        "results": results,
        "conclusion": conclusion,
        "full_sections": full_sections,
        "errors": errors,
    }
