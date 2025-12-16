import httpx
from typing import List
from datetime import datetime
from bs4 import BeautifulSoup
from app.services.fetcher_base import BaseFetcher
from app.schemas.article import ArticleCreate

class ProductHuntFetcher(BaseFetcher):
    FEED_URL = "https://www.producthunt.com/feed"

    @property
    def source_name(self) -> str:
        return "Product Hunt"

    async def fetch_latest(self, limit: int = 10) -> List[ArticleCreate]:
        # trust_env=False to avoid inheriting local proxy env that can break fetches without socks support
        async with httpx.AsyncClient(trust_env=False) as client:
            try:
                resp = await client.get(self.FEED_URL)
                resp.raise_for_status()
                
                # Use XML parser
                soup = BeautifulSoup(resp.content, 'xml')
                entries = soup.find_all(['entry', 'item'])
                
                articles = []
                for entry in entries[:limit]:
                    title = entry.find('title').text if entry.find('title') else "No Title"
                    link_tag = entry.find('link')
                    # Atom feeds have href attr, RSS has text content
                    url = link_tag['href'] if link_tag.has_attr('href') else link_tag.text
                    
                    # Clean up URL (remove query params for cleaner ID)
                    base_url = url.split('?')[0]
                    
                    # Extract date
                    published = entry.find(['published', 'pubDate'])
                    pub_date = datetime.now() # Fallback
                    # (Parsing logic for date strings can be added here if needed)

                    articles.append(ArticleCreate(
                        title=title,
                        url=base_url,
                        source="Product Hunt",
                        source_id=base_url.split('/')[-1],
                        publish_date=pub_date
                    ))
                
                return articles

            except Exception as e:
                print(f"Error fetching Product Hunt RSS: {e}")
                return []
