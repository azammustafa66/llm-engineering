"""Website scrapers used by the week-1 notebooks.

Two ways to turn a page into clean, token-friendly text for an LLM prompt:

- `fetch_website_content` — fast static fetch via `requests` (no JavaScript).
- `SeleniumScraper`       — drives a real Chrome browser for JS-rendered pages.

Both funnel through `clean_html`, so the cleaning logic lives in one place.
"""

from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Pretend to be a real browser so sites don't block the request with a 403.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)
headers = {"User-Agent": USER_AGENT}

# Tags whose contents are noise for summarization (code, styling, media, forms).
IRRELEVANT_TAGS = ["script", "style", "img", "input"]


def clean_html(html: str | bytes) -> str:
    """Strip a raw HTML document down to its title and visible text.

    Removes scripts, styles, images and form inputs, then collapses the
    remaining DOM into newline-separated, trimmed text. Use this to turn any
    HTML source (from `requests`, Selenium, a file, ...) into a compact,
    token-friendly string suitable for an LLM prompt.

    Args:
        html: The raw HTML markup to clean.

    Returns:
        The page title followed by its cleaned, visible text.
    """
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string if soup.title else "No title found"

    # Strip out elements that don't contribute readable content.
    for irrelevant_tag in soup(IRRELEVANT_TAGS):
        irrelevant_tag.decompose()

    # Collapse the remaining DOM into newline-separated, trimmed text.
    text = soup.get_text(separator="\n", strip=True)
    return f"Title: {title}\n\n{text}"


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
        return clean_html(response.content)
    except Exception as e:
        return f"Error fetching content from {url}: {str(e)}"


def extract_links(html: str | bytes, base_url: str) -> list[str]:
    """Pull every hyperlink out of an HTML document as absolute URLs.

    Relative hrefs are resolved against ``base_url``, and non-navigational
    links (page anchors, ``mailto:``, ``tel:``, ``javascript:``) are skipped.
    The result is de-duplicated while preserving first-seen order.

    Args:
        html: The raw HTML markup to scan.
        base_url: The page's URL, used to turn relative links absolute.

    Returns:
        A list of absolute URLs found in the page.
    """
    soup = BeautifulSoup(html, "html.parser")

    links: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = str(anchor["href"]).strip()
        # Drop empty hrefs and ones that don't point at another page.
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        links.append(urljoin(base_url, href))  # "/about" -> "https://site.com/about"

    # dict.fromkeys de-duplicates while keeping the original order.
    return list(dict.fromkeys(links))


def fetch_website_links(url: str, extract: bool = False) -> list[str] | str:
    """Fetch a page and return all hyperlinks inside it as absolute URLs.

    Args:
        url: The URL of the website to fetch.

    Returns:
        A list of absolute URLs, or the raw HTML content if `extract` is False.
    """
    try:
        response = requests.get(url=url, headers=headers, timeout=10)
        response.raise_for_status()
        return extract_links(response.content, base_url=url) if extract else response.text
    except Exception as e:
        print(f"Error fetching links from {url}: {e}")
        return []


class SeleniumScraper:
    """Fetch a JS-rendered page with Selenium.

    Use this instead of `fetch_website_content` when a site builds its content
    with JavaScript (single-page apps, infinite scroll, ...), which a plain
    `requests` call can't see.

    Typical usage:
        scraper = SeleniumScraper(url="https://example.com")
        scraper.fetch_content()
        print(scraper.text)
    """

    def __init__(self, url: str) -> None:
        self.url = url
        self.text: str | None = None  # cleaned page text, filled by fetch_content

    def fetch_content(self) -> None:
        """Load the page in Chrome and store the cleaned, visible text."""
        options = Options()
        options.add_argument(f"User-Agent={USER_AGENT}")
        driver = webdriver.Chrome(options=options)
        try:
            driver.get(url=self.url)
            driver.implicitly_wait(5)  # give JS up to 5s to populate the DOM
            # Reuse the shared cleaner so we send far fewer tokens to the model.
            self.text = clean_html(driver.page_source)
        except Exception as e:
            print(f"Error fetching content with Selenium: {e}")
        finally:
            driver.quit()  # always release the browser, even on error
