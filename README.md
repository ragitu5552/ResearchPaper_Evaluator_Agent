# Agentic Research Paper Evaluator

A multi-agent AI system that autonomously audits arXiv research papers using LangGraph and Groq (Llama 3.3 70B).

## Architecture

```
START
  │
  ▼
scraper_node          — fetches arXiv HTML, extracts title/authors/text
  │
  ▼
decomposer_node       — splits paper into Abstract / Methodology / Results / Conclusion
  │
  ├─► consistency_node    ─┐
  ├─► grammar_node         │  (parallel fan-out via LangGraph conditional edges)
  ├─► novelty_node         │
  ├─► fact_checker_node    │
  └─► authenticity_node   ─┘
                            │
                            ▼
                      aggregator_node   — validates outputs, fills defaults
                            │
                            ▼
                   report_generator_node — Markdown + PDF report
                            │
                            ▼
                           END
```

## Agents

| Agent | What it evaluates |
|-------|------------------|
| **Consistency** | Does the methodology logically support the claimed results? (0–100 score) |
| **Grammar** | Academic tone, clarity, and writing quality (High / Medium / Low) |
| **Novelty** | Specificity of novel contributions claimed by the paper |
| **Fact Checker** | Extracts up to 8 verifiable claims and flags each as verified / unverified / suspicious |
| **Authenticity** | Fabrication probability based on statistical anomalies and red flags (0–100%) |

## Setup

```bash
git clone <repo-url>
cd research-evaluator

py -3.11 -m venv venv311
venv311\Scripts\activate        # Windows
# source venv311/bin/activate   # Mac/Linux

pip install -r requirements.txt

cp .env.example .env
# Add your GROQ_API_KEY to .env  →  https://console.groq.com
```

## Running

```bash
streamlit run ui/app.py
```

## Running Tests

```bash
pytest tests/ -v
```

## Design Decisions

- **Why LangGraph:** explicit StateGraph with typed state, native fan-out/fan-in for parallel agents, and clean node isolation
- **Why Groq (Llama 3.3 70B):** generous free tier, very fast inference, handles JSON-structured outputs reliably
- **Why fpdf2:** zero system dependencies, pure Python PDF generation — no wkhtmltopdf or LaTeX required
- **16k token constraint:** enforced in `utils/chunker.py` via `truncate_to_limit()` before every LLM call
- **Error accumulation:** `state["errors"]` uses `Annotated[list, operator.add]` so parallel agents each append their own errors without conflict

## Known Limitations

- Novelty agent uses LLM reasoning about claimed contributions — not a live literature search
- Fact-checking is LLM-based inference, not against a verified external knowledge base
- Decomposer falls back to LLM splitting for arXiv HTML papers (regex is unreliable due to TOC structure)
- PDF rendering is minimal — content over aesthetics
