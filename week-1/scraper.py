"""Lightweight website scraper used by the week-1 notebooks.

Fetches a page over HTTP and returns a clean, text-only representation
(title + visible body text) that is suitable for feeding into an LLM prompt.
"""

import requests
from bs4 import BeautifulSoup

# Pretend to be a real browser so sites don't block the request with a 403.
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Tags whose contents are noise for summarization (code, styling, media, forms).
IRRELEVANT_TAGS = ["script", "style", "img", "input"]


def fetch_website_content(url: str) -> str:
    """Fetch a website and return its title and visible text as a single string.

    Args:
        url: The URL of the website to fetch.

    Returns:
        The page title followed by its cleaned, visible text. On failure,
        returns a human-readable error string instead of raising.
    """
    try:
        response = requests.get(url=url, headers=headers, timeout=10)
        response.raise_for_status()  # turn 4xx/5xx responses into exceptions

        soup = BeautifulSoup(response.content, "html.parser")
        title = soup.title.string if soup.title else "No title found"

        # Strip out elements that don't contribute readable content.
        for irrelevant_tag in soup(IRRELEVANT_TAGS):
            irrelevant_tag.decompose()

        # Collapse the remaining DOM into newline-separated, trimmed text.
        text = soup.get_text(separator="\n", strip=True)
        return f"Title: {title}\n\n{text}"
    except Exception as e:
        return f"Error fetching content from {url}: {str(e)}"
