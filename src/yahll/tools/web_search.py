try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS


def web_search(query: str, max_results: int = 5) -> dict:
    """Search the web using DuckDuckGo. No API key needed."""
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
        return {"results": results, "query": query}
    except Exception as e:
        return {"results": [], "error": str(e), "query": query}


def web_news(query: str, max_results: int = 5) -> dict:
    """Search for recent news using DuckDuckGo."""
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.news(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("body", ""),
                    "date": r.get("date", ""),
                })
        return {"results": results, "query": query}
    except Exception as e:
        return {"results": [], "error": str(e), "query": query}
