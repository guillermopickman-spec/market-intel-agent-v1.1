import requests
import textwrap
from core.settings import settings
from core.logger import get_logger

logger = get_logger("NotionService")

class NotionService:
    def __init__(self):
        self.token = settings.NOTION_TOKEN
        self.page_id = settings.NOTION_PAGE_ID
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

    def create_page(self, title: str, content: str) -> bool:
        """
        Creates a formatted report in Notion. 
        Renamed from 'send_report' to 'create_page' for Router compatibility.
        """
        url = f"https://api.notion.com/v1/blocks/{self.page_id}/children"
        
        paragraphs = textwrap.wrap(content, width=1900, replace_whitespace=False)
        children = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": f"📌 AI Agent Report: {title}"}}]}
            }
        ]

        for p in paragraphs:
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": p}}]}
            })

        try:
            response = requests.patch(
                url, 
                headers=self.headers, 
                json={"children": children},
                timeout=settings.HTTP_REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return True
        except requests.Timeout:
            logger.error(f"Notion API request timed out after {settings.HTTP_REQUEST_TIMEOUT}s")
            return False
        except Exception as e:
            logger.error(f"Notion Service Error: {e}", exc_info=True)
            return False