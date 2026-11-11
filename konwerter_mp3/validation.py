from __future__ import annotations

from urllib.parse import urlparse

YOUTUBE_HOSTS = frozenset({
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
})


def is_valid_youtube_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    if not url:
        return False
    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    if parsed.scheme not in ("http", "https"):
        return False

    host = (parsed.netloc or "").lower().split(":", 1)[0]
    if host.startswith("www."):
        host_full = host
    else:
        host_full = host
    if host_full not in YOUTUBE_HOSTS:
        return False

    if host_full == "youtu.be":
        return len(parsed.path.strip("/")) > 0

    path = parsed.path or ""
    query = parsed.query or ""

    if path in ("/watch", "/watch/") and "v=" in query:
        return True
    for prefix in ("/shorts/", "/live/", "/embed/", "/v/"):
        if path.startswith(prefix) and len(path) > len(prefix):
            return True
    return False
