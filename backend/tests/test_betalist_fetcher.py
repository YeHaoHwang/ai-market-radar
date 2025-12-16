import httpx
import pytest

from app.services.betalist_fetcher import BetaListFetcher


SAMPLE_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>BetaList</title>
    <item>
      <title>Startup One</title>
      <link>https://betalist.com/startups/startup-one</link>
      <guid>startup-one</guid>
    </item>
    <item>
      <title>Startup Two</title>
      <link>https://betalist.com/startups/startup-two</link>
      <guid>startup-two</guid>
    </item>
  </channel>
</rss>
"""


def make_client_factory(transport: httpx.MockTransport):
    def _factory(**kwargs):
        return httpx.AsyncClient(transport=transport, **kwargs)
    return _factory


@pytest.mark.asyncio
async def test_betalist_follows_redirect_and_parses_items():
    def handler(request: httpx.Request) -> httpx.Response:
        # First URL returns 301; client should follow to the startups feed.
        if str(request.url) == "https://betalist.com/rss":
            return httpx.Response(
                status_code=301,
                headers={"Location": "https://betalist.com/startups/feed"},
            )
        if str(request.url) == "https://betalist.com/startups/feed":
            return httpx.Response(200, text=SAMPLE_FEED)
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    fetcher = BetaListFetcher(client_factory=make_client_factory(transport))

    articles = await fetcher.fetch_latest(limit=2)

    assert len(articles) == 2
    assert articles[0].title == "Startup One"
    assert articles[0].url == "https://betalist.com/startups/startup-one"
    assert articles[0].source == fetcher.source_name
