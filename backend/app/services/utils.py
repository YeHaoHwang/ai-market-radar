from urllib.parse import urlparse, urlunparse

def normalize_url(url: str) -> str:
    """Normalize URLs to improve cross-platform deduping."""
    if not url:
        return url

    parsed = urlparse(url.strip())

    scheme = (parsed.scheme or "http").lower()
    netloc = parsed.netloc.lower()
    # ensure path not empty; remove trailing slash
    path = parsed.path.rstrip("/") or "/"

    normalized = urlunparse((
        scheme,
        netloc,
        path,
        "",  # params
        "",  # query
        "",  # fragment
    ))
    return normalized
