import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os
from dotenv import load_dotenv
from rich import print
from langchain.tools import tool

load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

@tool
def web_search(query: str) -> str:
    """Search the web for the given query and return the results."""
    
    results = tavily.search(query=query, max_results=5)

    if not results:
        return "No results found."
    return str(results)

@tool
def web_scrape(url: str) -> str:
    """Scrape the content of the given URL and return the text."""
    try:
     resp = requests.get(url,timeout=8,headers={'User-Agent': 'Mozilla/5.0'})
     soup = BeautifulSoup(resp.text, 'html.parser')
     for tag in soup(['script', 'style','nav','footer','header','aside']):
        tag.decompose()
     text = soup.get_text(separator='',strip = True)[:3000]
     return text
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"
if __name__ == "__main__":
    print(web_scrape.invoke("https://en.wikipedia.org/wiki/Artificial_intelligence"))
