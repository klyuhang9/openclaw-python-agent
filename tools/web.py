import requests
from typing import Optional

try:
    from ddgs import DDGS
    HAS_DDGS = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        HAS_DDGS = True
    except ImportError:
        HAS_DDGS = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo and return titles, URLs, and snippets."""
    if not HAS_DDGS:
        return "Error: duckduckgo-search package not installed"
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(
                    f"Title: {r.get('title', '')}\n"
                    f"URL: {r.get('href', '')}\n"
                    f"Snippet: {r.get('body', '')}"
                )
        if not results:
            return "No results found"
        return "\n\n---\n\n".join(results)
    except Exception as e:
        return f"Error performing web search: {e}"


def scrape_webpage(url: str, timeout: int = 15) -> str:
    """Fetch a webpage and extract the main text content using BeautifulSoup."""
    if not HAS_BS4:
        return "Error: beautifulsoup4 package not installed"
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script/style elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # Collapse excessive blank lines
        lines = [line for line in text.splitlines() if line.strip()]
        text = "\n".join(lines)

        # Limit output size
        if len(text) > 8000:
            text = text[:8000] + "\n...[truncated]"

        return text
    except requests.Timeout:
        return f"Error: Request timed out after {timeout} seconds"
    except requests.HTTPError as e:
        return f"Error: HTTP {e.response.status_code} for {url}"
    except Exception as e:
        return f"Error scraping webpage: {e}"
