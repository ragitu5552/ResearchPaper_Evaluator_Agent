import re
import requests
from bs4 import BeautifulSoup
from graph.state import PaperState


def _extract_paper_id(url: str) -> str:
    """Extract arXiv paper ID from various URL formats."""
    match = re.search(r'arxiv\.org/(?:abs|html|pdf)/([0-9]+\.[0-9]+)', url)
    if match:
        return match.group(1)
    raise ValueError(f"Could not extract arXiv ID from URL: {url}")


def scrape_paper(state: PaperState) -> dict:
    """
    Fetch arXiv paper, extract clean text, title, and authors.
    Returns: {"raw_text": str, "paper_title": str, "paper_authors": str}
    """
    errors = []

    try:
        paper_id = _extract_paper_id(state["arxiv_url"])
    except ValueError as e:
        errors.append(str(e))
        return {"raw_text": "", "paper_title": "", "paper_authors": "", "errors": errors}

    title = ""
    authors = ""
    raw_text = ""

    # --- Step 1: Get metadata from abs page ---
    try:
        abs_url = f"https://arxiv.org/abs/{paper_id}"
        resp = requests.get(abs_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        title_tag = soup.find("h1", class_="title")
        if title_tag:
            title = title_tag.get_text(strip=True).replace("Title:", "").strip()

        authors_tag = soup.find("div", class_="authors")
        if authors_tag:
            authors = authors_tag.get_text(strip=True).replace("Authors:", "").strip()
    except Exception as e:
        errors.append(f"Metadata fetch failed: {e}")

    # --- Step 2: Get full text from HTML version ---
    try:
        html_url = f"https://arxiv.org/html/{paper_id}"
        resp = requests.get(html_url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Remove unwanted elements
        for tag in soup.find_all(["script", "style", "figure", "table"]):
            tag.decompose()
        # Remove reference section
        for tag in soup.find_all(["section", "div"], id=re.compile(r'ref', re.I)):
            tag.decompose()
        for tag in soup.find_all(["h2", "h3"], string=re.compile(r'references?', re.I)):
            # Remove the references section from this heading onward
            for sibling in tag.find_all_next():
                sibling.decompose()
            tag.decompose()

        raw_text = soup.get_text(separator="\n")
        # Clean up whitespace
        raw_text = re.sub(r'\n{3,}', '\n\n', raw_text).strip()

    except Exception as e:
        errors.append(f"HTML fetch failed ({e}), trying abs page text as fallback.")
        # Fallback: use abstract page text
        try:
            abs_url = f"https://arxiv.org/abs/{paper_id}"
            resp = requests.get(abs_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            abstract_block = soup.find("blockquote", class_="abstract")
            if abstract_block:
                raw_text = abstract_block.get_text(strip=True).replace("Abstract:", "").strip()
            else:
                raw_text = soup.get_text(separator="\n")
                raw_text = re.sub(r'\n{3,}', '\n\n', raw_text).strip()
        except Exception as e2:
            errors.append(f"Fallback fetch also failed: {e2}")
            raw_text = ""

    return {
        "raw_text": raw_text,
        "paper_title": title,
        "paper_authors": authors,
        "errors": errors,
    }
