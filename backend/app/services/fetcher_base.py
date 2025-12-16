from abc import ABC, abstractmethod
from typing import List
from app.schemas.article import ArticleCreate

class BaseFetcher(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str:
        """The name of the data source."""
        pass

    @abstractmethod
    async def fetch_latest(self, limit: int = 10) -> List[ArticleCreate]:
        """Fetch latest articles from the source."""
        pass
