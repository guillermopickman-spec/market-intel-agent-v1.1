from ddgs import DDGS
from core.logger import get_logger

logger = get_logger("SearchService")

class SearchService:
    def search(self, query: str) -> str:
        """Fallback search when direct scraping is blocked."""
        try:
            logger.info(f"🔍 Plan B: Searching the web for '{query}'")
            with DDGS() as ddgs:
                results = [f"{r['title']}: {r['body']} (Source: {r['href']})" for r in ddgs.text(query, max_results=5)]
                if not results:
                    return "No search results found."
                return "\n\n".join(results)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return f"Search error: {str(e)}"