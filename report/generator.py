from datetime import datetime
from graph.state import PaperState


def _verdict(state: PaperState) -> str:
    consistency = state.get("consistency_score") or 0
    grammar = state.get("grammar_rating") or "Low"
    authenticity = state.get("authenticity_score") or 50.0

    if consistency >= 70 and grammar != "Low" and authenticity <= 30:
        return "PASS"
    elif consistency < 50 or authenticity > 70:
        return "FAIL"
    else:
        return "CONDITIONAL PASS"


def _fact_table(fact_check_log: list) -> str:
    if not fact_check_log:
        return "_No facts extracted._"

    status_icon = {
        "verified": "✅ Verified",
        "unverified": "❌ Unverified",
        "suspicious": "⚠️ Suspicious",
    }

    rows = ["| Claim | Status | Note |", "|-------|--------|------|"]
    for item in fact_check_log:
        claim = item.get("claim", "").replace("|", "\\|")
        status = status_icon.get(item.get("status", "unverified"), "❌ Unverified")
        note = item.get("note", "").replace("|", "\\|")
        rows.append(f"| {claim} | {status} | {note} |")

    return "\n".join(rows)


def _executive_summary(state: PaperState, verdict: str) -> str:
    consistency = state.get("consistency_score") or 0
    grammar = state.get("grammar_rating") or "Low"
    novelty = state.get("novelty_index") or "Unclear"
    authenticity = state.get("authenticity_score") or 50.0

    lines = [f"**Verdict: {verdict}**", ""]
    lines.append(
        f"The paper scores **{consistency}/100** on internal consistency and receives a "
        f"**{grammar}** grammar rating. "
        f"Novelty is assessed as **{novelty}**, with a fabrication risk of **{authenticity:.1f}%**. "
    )
    if verdict == "PASS":
        lines.append("Overall, the paper appears well-structured, credible, and ready for peer review.")
    elif verdict == "FAIL":
        lines.append("Significant issues were identified that require substantial revision before publication.")
    else:
        lines.append("The paper shows promise but requires targeted improvements before it is publication-ready.")

    return "\n".join(lines)


def generate_report(state: PaperState) -> str:
    verdict = _verdict(state)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    # Extract red flags from authenticity reasoning if present
    auth_reasoning = state.get("authenticity_reasoning") or "No assessment available."
    red_flags_section = ""
    if "\nRed Flags:\n" in auth_reasoning:
        parts = auth_reasoning.split("\nRed Flags:\n", 1)
        auth_reasoning_clean = parts[0].strip()
        red_flags_section = "\n**Red Flags Identified:**\n" + parts[1].strip()
    else:
        auth_reasoning_clean = auth_reasoning

    errors = state.get("errors") or []
    errors_section = "\n".join(f"- {e}" for e in errors) if errors else "_None_"

    report = f"""# Judgement Report: {state.get("paper_title", "Unknown Paper")}
**Authors:** {state.get("paper_authors", "Unknown")}
**arXiv URL:** {state.get("arxiv_url", "")}
**Evaluated on:** {timestamp}

---

## Executive Summary

{_executive_summary(state, verdict)}

---

## Detailed Scores

### Consistency Score: {state.get("consistency_score", 0)}/100
{state.get("consistency_reasoning") or "No assessment available."}

### Grammar Rating: {state.get("grammar_rating", "Low")}
{state.get("grammar_reasoning") or "No assessment available."}

### Novelty Index: {state.get("novelty_index", "Unclear")}
{state.get("novelty_reasoning") or "No assessment available."}

### Fact Check Log
{_fact_table(state.get("fact_check_log") or [])}

### Authenticity / Fabrication Score: {state.get("authenticity_score", 50.0):.1f}% fabrication risk
{auth_reasoning_clean}{red_flags_section}

---

## Errors During Evaluation
{errors_section}
"""
    return report.strip()
