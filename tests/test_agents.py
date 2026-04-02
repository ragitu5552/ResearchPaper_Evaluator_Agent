import pytest

SAMPLE_STATE = {
    "arxiv_url": "https://arxiv.org/abs/1706.03762",
    "raw_text": "",
    "paper_title": "Test Paper",
    "paper_authors": "Test Author",
    "abstract": (
        "We propose a novel Transformer architecture based entirely on attention mechanisms, "
        "dispensing with recurrence and convolutions entirely. The model achieves state-of-the-art "
        "results on machine translation tasks, with 28.4 BLEU on WMT 2014 English-to-German."
    ),
    "methodology": (
        "The Transformer uses stacked self-attention and point-wise fully connected layers for both "
        "encoder and decoder. The encoder maps input sequence to continuous representations. "
        "Multi-head attention allows the model to jointly attend to information from different "
        "representation subspaces. We use 8 attention heads with d_model=512. "
        "Positional encodings are added to inject sequence order information. "
        "Training used the Adam optimizer with a custom learning rate schedule and dropout of 0.1."
    ),
    "results": (
        "Our model achieves 28.4 BLEU on WMT 2014 English-to-German, surpassing all previously "
        "published models including ensembles, by more than 2 BLEU. On English-to-French we achieve "
        "41.0 BLEU, outperforming all prior single models at less than 1/4 the training cost. "
        "Training took 3.5 days on 8 P100 GPUs."
    ),
    "conclusion": (
        "In this work we presented the Transformer, the first sequence transduction model based "
        "entirely on attention, replacing the recurrent layers most commonly used in encoder-decoder "
        "architectures with multi-headed self-attention. We plan to apply the Transformer to other "
        "modalities and investigate local attention mechanisms."
    ),
    "full_sections": {},
    "errors": [],
    "consistency_score": None,
    "consistency_reasoning": None,
    "grammar_rating": None,
    "grammar_reasoning": None,
    "novelty_index": None,
    "novelty_reasoning": None,
    "fact_check_log": None,
    "authenticity_score": None,
    "authenticity_reasoning": None,
    "report_markdown": None,
    "report_pdf_path": None,
}


def test_consistency_agent():
    from agents.consistency_agent import check_consistency
    result = check_consistency(SAMPLE_STATE)
    assert isinstance(result["consistency_score"], int)
    assert 0 <= result["consistency_score"] <= 100
    assert isinstance(result["consistency_reasoning"], str)
    assert len(result["consistency_reasoning"]) > 10


def test_grammar_agent():
    from agents.grammar_agent import check_grammar
    result = check_grammar(SAMPLE_STATE)
    assert result["grammar_rating"] in ("High", "Medium", "Low")
    assert isinstance(result["grammar_reasoning"], str)


def test_novelty_agent():
    from agents.novelty_agent import assess_novelty
    result = assess_novelty(SAMPLE_STATE)
    assert result["novelty_index"] in ("Highly Novel", "Moderately Novel", "Incremental", "Unclear")
    assert isinstance(result["novelty_reasoning"], str)


def test_fact_checker_agent():
    from agents.fact_checker_agent import check_facts
    result = check_facts(SAMPLE_STATE)
    assert isinstance(result["fact_check_log"], list)
    for item in result["fact_check_log"]:
        assert "claim" in item
        assert item["status"] in ("verified", "unverified", "suspicious")
        assert "note" in item


def test_authenticity_agent():
    from agents.authenticity_agent import check_authenticity
    result = check_authenticity(SAMPLE_STATE)
    assert isinstance(result["authenticity_score"], float)
    assert 0.0 <= result["authenticity_score"] <= 100.0
    assert isinstance(result["authenticity_reasoning"], str)
