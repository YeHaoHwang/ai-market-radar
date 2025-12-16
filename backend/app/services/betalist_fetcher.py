import httpx
import logging
from typing import Callable, List
from datetime import datetime
from bs4 import BeautifulSoup
from app.services.fetcher_base import BaseFetcher
from app.schemas.article import ArticleCreate

logger = logging.getLogger(__name__)

class BetaListFetcher(BaseFetcher):
    RSS_URL = "https://betalist.com/rss"
    FALLBACK_URL = "https://betalist.com/startups/feed"

    def __init__(self, client_factory: Callable[..., httpx.AsyncClient] | None = None) -> None:
        # 允许在测试中注入自定义 AsyncClient（例如 MockTransport）
        self.client_factory = client_factory or httpx.AsyncClient

    @property
    def source_name(self) -> str:
        return "BetaList"

    async def _get_feed(self, client: httpx.AsyncClient, url: str) -> httpx.Response:
        return await client.get(url, follow_redirects=True)

    async def fetch_latest(self, limit: int = 10) -> List[ArticleCreate]:
        # trust_env=False 避免继承本地代理；follow_redirects 处理 301 -> startups/feed
        async with self.client_factory(trust_env=False, follow_redirects=True) as client:
            try:
                resp = await self._get_feed(client, self.RSS_URL)
                if resp.status_code != 200:
                    resp = await self._get_feed(client, self.FALLBACK_URL)
                resp.raise_for_status()
                
                soup = BeautifulSoup(resp.content, "xml")
                items = soup.find_all("item")
                
                articles = []
                for item in items[:limit]:
                    title = item.find("title").text if item.find("title") else "No Title"
                    link = item.find("link").text if item.find("link") else ""
                    
                    if not link:
                        continue

                    # Extract GUID or use link as ID
                    guid = item.find("guid")
                    source_id = guid.text if guid else link
                    
                    articles.append(ArticleCreate(
                        title=title,
                        url=link,
                        source=self.source_name,
                        source_id=source_id,
                        publish_date=datetime.now()  # RSS often misses pubDate; ingestion time is safer
                    ))
                
                return articles

            except Exception as e:
                logger.error("Error fetching BetaList: %r", e)
                return []
