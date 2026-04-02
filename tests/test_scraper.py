import pytest
from agents.scraper import scrape_paper, _extract_paper_id


def test_extract_paper_id_abs_url():
    assert _extract_paper_id("https://arxiv.org/abs/1706.03762") == "1706.03762"


def test_extract_paper_id_html_url():
    assert _extract_paper_id("https://arxiv.org/html/1706.03762") == "1706.03762"


def test_extract_paper_id_invalid():
    with pytest.raises(ValueError):
        _extract_paper_id("https://example.com/not-arxiv")


def test_scrape_paper_returns_title():
    result = scrape_paper({"arxiv_url": "https://arxiv.org/abs/1706.03762", "errors": []})
    assert "Attention" in result["paper_title"]
    assert result["paper_authors"] != ""
    assert len(result["raw_text"]) > 1000
    assert result["errors"] == []


def test_scrape_paper_invalid_url():
    result = scrape_paper({"arxiv_url": "https://example.com/bad", "errors": []})
    assert result["raw_text"] == ""
    assert len(result["errors"]) > 0
