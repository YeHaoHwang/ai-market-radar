import httpx
from typing import List
from datetime import datetime
from app.services.fetcher_base import BaseFetcher
from app.schemas.article import ArticleCreate

class HuggingFaceFetcher(BaseFetcher):
    # API to get trending spaces
    API_URL = "https://huggingface.co/api/spaces"

    @property
    def source_name(self) -> str:
        return "Hugging Face"

    async def fetch_latest(self, limit: int = 10) -> List[ArticleCreate]:
        async with httpx.AsyncClient() as client:
            try:
                # Sort by likes (trending)
                params = {
                    "sort": "likes",
                    "direction": "-1",
                    "limit": limit
                }
                resp = await client.get(self.API_URL, params=params)
                resp.raise_for_status()
                
                data = resp.json()
                
                articles = []
                for rank, item in enumerate(data, start=1):
                    # HF API returns list of objects
                    space_id = item.get("id") # e.g. "facebook/musicgen"
                    likes = item.get("likes", 0)
                    
                    if not space_id:
                        continue
                        
                    full_url = f"https://huggingface.co/spaces/{space_id}"
                    
                    # Create a descriptive title
                    title = f"{space_id} (Space)"
                    
                    articles.append(ArticleCreate(
                        title=title,
                        url=full_url,
                        source=self.source_name,
                        source_id=space_id,
                        publish_date=datetime.now(),
                        current_metric_value=likes,
                        current_rank=rank
                    ))
                
                return articles

            except Exception as e:
                print(f"Error fetching Hugging Face: {e}")
                return []
