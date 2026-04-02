import re
import requests
from bs4 import BeautifulSoup
from graph.state import PaperState

HEADERS = {"User-Agent": "Mozilla/5.0"}
MIN_FULL_TEXT_CHARS = 3000  # below this we consider the HTML version incomplete


def _extract_paper_id(url: str) -> str:
    """Extract arXiv paper ID from various URL formats."""
    match = re.search(r'arxiv\.org/(?:abs|html|pdf)/([0-9]+\.[0-9]+(?:v\d+)?)', url)
    if match:
        return match.group(1)
    raise ValueError(f"Could not extract arXiv ID from URL: {url}")


def _clean_soup(soup: BeautifulSoup) -> str:
    for tag in soup.find_all(["script", "style", "figure", "table"]):
        tag.decompose()
    for tag in soup.find_all(["section", "div"], id=re.compile(r'ref', re.I)):
        tag.decompose()
    for tag in soup.find_all(["h2", "h3"], string=re.compile(r'^references?$', re.I)):
        for sibling in tag.find_all_next():
            sibling.decompose()
        tag.decompose()
    text = soup.get_text(separator="\n")
    return re.sub(r'\n{3,}', '\n\n', text).strip()


def _fetch_html_version(paper_id: str) -> str:
    """Try fetching the full HTML version of the paper (multiple URL variants)."""
    base_id = re.sub(r'v\d+$', '', paper_id)  # strip version suffix for HTML url
    candidates = [
        f"https://arxiv.org/html/{base_id}",
        f"https://arxiv.org/html/{base_id}v1",
        f"https://arxiv.org/html/{base_id}v2",
    ]
    for url in candidates:
        try:
            resp = requests.get(url, timeout=20, headers=HEADERS)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "lxml")
                text = _clean_soup(soup)
                if len(text) >= MIN_FULL_TEXT_CHARS:
                    return text
        except Exception:
            continue
    return ""


def _fetch_abs_metadata(paper_id: str) -> tuple[str, str, str]:
    """Fetch title, authors, and abstract text from the abs page."""
    abs_url = f"https://arxiv.org/abs/{paper_id}"
    resp = requests.get(abs_url, timeout=15, headers=HEADERS)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    title_tag = soup.find("h1", class_="title")
    title = title_tag.get_text(strip=True).replace("Title:", "").strip() if title_tag else ""

    authors_tag = soup.find("div", class_="authors")
    authors = authors_tag.get_text(strip=True).replace("Authors:", "").strip() if authors_tag else ""

    abstract_block = soup.find("blockquote", class_="abstract")
    abstract = abstract_block.get_text(strip=True).replace("Abstract:", "").strip() if abstract_block else ""

    return title, authors, abstract


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

    # Step 1: metadata from abs page
    title, authors, abstract_text = "", "", ""
    try:
        title, authors, abstract_text = _fetch_abs_metadata(paper_id)
    except Exception as e:
        errors.append(f"Metadata fetch failed: {e}")

    # Step 2: try full HTML version
    raw_text = _fetch_html_version(paper_id)

    # Step 3: if no HTML available, use abstract as raw_text and note it
    if not raw_text:
        if abstract_text:
            errors.append(
                "HTML version not available for this paper (likely too new). "
                "Evaluating abstract only — section-level scores will be limited."
            )
            raw_text = f"Abstract\n\n{abstract_text}"
        else:
            errors.append("Could not retrieve any text for this paper.")

    return {
        "raw_text": raw_text,
        "paper_title": title,
        "paper_authors": authors,
        "errors": errors,
    }
