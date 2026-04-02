# Agentic Research Paper Evaluator

> Paste any arXiv URL. Get a structured AI audit in under 60 seconds — consistency score, grammar rating, novelty index, fact check log, and fabrication risk — delivered as a live Streamlit report with PDF download.

Built with **LangGraph** (parallel multi-agent orchestration) + **Groq Llama 3.3 70B** (free-tier LLM) + **Streamlit** UI.

---

## Architecture

```
START
  │
  ▼
scraper_node          — fetches arXiv HTML, extracts title/authors/full text
  │
  ▼
decomposer_node       — splits paper into Abstract / Methodology / Results / Conclusion
  │
  ├─► consistency_node    ─┐
  ├─► grammar_node         │  5 agents run IN PARALLEL (LangGraph fan-out)
  ├─► novelty_node         │
  ├─► fact_checker_node    │
  └─► authenticity_node   ─┘
                            │
                            ▼
                      aggregator_node   — validates all outputs, fills safe defaults on failure
                            │
                            ▼
                   report_generator_node — compiles Markdown + exports PDF
                            │
                            ▼
                           END
```

## Agents

| Agent | Output | What it evaluates |
|-------|--------|------------------|
| **Consistency** | 0–100 score | Does the methodology logically support the claimed results? |
| **Grammar** | High / Medium / Low | Academic tone, clarity, sentence structure, professional vocabulary |
| **Novelty** | Highly Novel / Moderately Novel / Incremental / Unclear | Specificity and differentiation of the paper's claimed contributions |
| **Fact Checker** | List of up to 8 claims | Flags numerical constants, benchmark scores, dataset stats as verified / unverified / suspicious |
| **Authenticity** | 0–100% fabrication risk | Detects statistical anomalies, round numbers, vague datasets, overclaiming |

**Verdict logic:**
- `PASS` → Consistency ≥ 70 AND Grammar ≠ Low AND Fabrication Risk ≤ 30%
- `FAIL` → Consistency < 50 OR Fabrication Risk > 70%
- `CONDITIONAL PASS` → everything else

---

## Setup

```bash
git clone https://github.com/YOUR_USERNAME/research-evaluator.git
cd research-evaluator

# Requires Python 3.11+
py -3.11 -m venv venv311
venv311\Scripts\activate        # Windows
# source venv311/bin/activate   # Mac/Linux

pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your free Groq API key → https://console.groq.com
```

## Running

```bash
streamlit run ui/app.py
```

Then open `http://localhost:8501`, paste an arXiv URL, and click **Evaluate Paper**.

## Running Tests

```bash
pytest tests/ -v
```

12 tests covering chunker utilities and all 5 agents.

---

## Design Decisions

- **Why LangGraph:** Explicit `StateGraph` with a typed `TypedDict` state schema. Native fan-out/fan-in via conditional edges gives true parallel agent execution — not just async threads.
- **Why Groq (Llama 3.3 70B):** Generous free tier (100k tokens/day), sub-second inference, reliable JSON-structured outputs. Swap the 3 lines in `utils/llm_client.py` to use any OpenAI-compatible provider.
- **Why fpdf2:** Zero system dependencies — no wkhtmltopdf, no LaTeX, no headless Chrome. Pure Python PDF generation.
- **16k token constraint:** Enforced in `utils/chunker.py` via `truncate_to_limit()` before every single LLM call. Each section is capped before being passed to any agent.
- **Error accumulation pattern:** `state["errors"]` uses `Annotated[list, operator.add]` so all 5 parallel agents can each append their own errors without LangGraph raising an `InvalidUpdateError`.

## Known Limitations

- Novelty agent uses LLM reasoning about claimed contributions — not a live literature search against real prior work
- Fact-checking is LLM-based plausibility assessment, not verified against an external knowledge base
- Papers without an HTML version on arXiv (very new submissions) are evaluated on abstract text only
- Decomposer uses LLM fallback for section splitting since arXiv HTML TOC structure breaks regex
- PDF rendering is functional but minimal — content-first, not design-first
- Groq free tier: 100k tokens/day limit; running the full pipeline costs ~15–20k tokens per paper
