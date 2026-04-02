import operator
from typing import TypedDict, Optional, Annotated


class PaperState(TypedDict):
    # --- Input ---
    arxiv_url: str

    # --- After scraper ---
    raw_text: str
    paper_title: str
    paper_authors: str

    # --- After decomposer ---
    abstract: str
    methodology: str
    results: str
    conclusion: str
    full_sections: dict          # {"abstract": str, "methodology": str, ...}

    # --- Agent outputs (filled in parallel) ---
    consistency_score: Optional[int]          # 0-100
    consistency_reasoning: Optional[str]

    grammar_rating: Optional[str]             # "High" | "Medium" | "Low"
    grammar_reasoning: Optional[str]

    novelty_index: Optional[str]              # qualitative description
    novelty_reasoning: Optional[str]

    fact_check_log: Optional[list]            # [{"claim": str, "status": str, "note": str}]

    authenticity_score: Optional[float]       # 0.0 - 100.0 (fabrication probability %)
    authenticity_reasoning: Optional[str]

    # --- Final output ---
    report_markdown: Optional[str]
    report_pdf_path: Optional[str]

    # --- Error tracking: Annotated so parallel agents can each append ---
    errors: Annotated[list, operator.add]
