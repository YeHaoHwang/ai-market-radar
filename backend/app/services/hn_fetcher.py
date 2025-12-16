import httpx
from typing import List
from datetime import datetime
from app.services.fetcher_base import BaseFetcher
from app.schemas.article import ArticleCreate

class HackerNewsFetcher(BaseFetcher):
    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    @property
    def source_name(self) -> str:
        return "Hacker News"

    async def fetch_latest(self, limit: int = 10) -> List[ArticleCreate]:
        # trust_env=False to avoid inheriting local proxy env that can break fetches without socks support
        async with httpx.AsyncClient(trust_env=False) as client:
            # 1. Get Top Stories IDs
            resp = await client.get(f"{self.BASE_URL}/topstories.json")
            resp.raise_for_status()
            story_ids = resp.json()[:limit]

            articles = []
            for rank, sid in enumerate(story_ids, start=1):
                # 2. Get Story Details
                try:
                    story_resp = await client.get(f"{self.BASE_URL}/item/{sid}.json")
                    if story_resp.status_code != 200:
                        continue
                    
                    data = story_resp.json()
                    if not data or "url" not in data:
                        continue

                    if data.get("type") != "story":
                        continue

                    article = ArticleCreate(
                        title=data.get("title", "No Title"),
                        url=data.get("url"),
                        source=self.source_name,
                        source_id=str(data.get("id")),
                        publish_date=datetime.fromtimestamp(data.get("time")) if data.get("time") else datetime.now(),
                        current_metric_value=data.get("score", 0),
                        current_rank=rank
                    )
                    articles.append(article)
                except Exception as e:
                    print(f"Error fetching HN story {sid}: {e}")
            
            return articles
