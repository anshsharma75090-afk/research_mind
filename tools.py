import time
import re

import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os
from dotenv import load_dotenv
from rich import print
from langchain.tools import tool
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

REQUEST_TIMEOUT = (6, 20)
MAX_ATTEMPTS = 3


def _requests_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=2,
        connect=2,
        read=2,
        status=2,
        backoff_factor=0.6,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "HEAD"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


http = _requests_session()


def _tavily_client() -> TavilyClient:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("Missing TAVILY_API_KEY in .env")
    return TavilyClient(api_key=api_key)


def _short_error(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"


def _clean_scraped_text(text: str) -> str:
    text = re.sub(r"https?://\S+", " ", text or "")
    text = re.sub(r"\[\s*\d+\s*\]", " ", text)
    text = re.sub(r"\[\s*(?:citation needed|edit|source)\s*\]", " ", text, flags=re.I)
    text = re.sub(r"\b(?:and\s+)?see\s+for\s+more\b", " ", text, flags=re.I)
    text = re.sub(r"\b(?:read|learn)\s+more\b", " ", text, flags=re.I)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

@tool
def web_search(query: str) -> str:
    """Search the web for the given query and return the results."""
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            # Build a fresh client for each run so long idle Streamlit sessions do
            # not reuse stale sockets that can trigger peer reset errors.
            results = _tavily_client().search(query=query, max_results=5)
            if not results:
                return "No results found."
            return str(results)
        except Exception as exc:
            last_error = exc
            if attempt < MAX_ATTEMPTS:
                time.sleep(1.5 * attempt)

    return f"Search temporarily failed after {MAX_ATTEMPTS} attempts: {_short_error(last_error)}"

@tool
def web_scrape(url: str) -> str:
    """Scrape the content of the given URL and return the text."""
    try:
        resp = http.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "close",
            },
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return _clean_scraped_text(text)[:5000]
    except Exception as e:
        return f"Error scraping {url}: {_short_error(e)}"
if __name__ == "__main__":
    print(web_scrape.invoke("https://en.wikipedia.org/wiki/Artificial_intelligence"))
