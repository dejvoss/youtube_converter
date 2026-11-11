from __future__ import annotations


class ConverterError(Exception):
    def __init__(self, user_message: str, detail: str = "") -> None:
        super().__init__(user_message)
        self.user_message = user_message
        self.detail = detail


_PATTERNS: tuple[tuple[tuple[str, ...], str], ...] = (
    (
        ("private video", "video is private"),
        "Film jest prywatny i nie można go pobrać.",
    ),
    (
        ("video has been removed", "video unavailable", "this video is no longer available"),
        "Film został usunięty lub jest niedostępny.",
    ),
    (
        ("confirm your age", "age-restricted", "age restricted", "sign in to confirm your age"),
        "Film ma ograniczenie wieku i nie można go pobrać bez logowania.",
    ),
    (
        ("members-only", "members only"),
        "Film jest dostępny tylko dla członków kanału.",
    ),
    (
        ("copyright",),
        "Film został zablokowany z powodu praw autorskich.",
    ),
    (
        (
            "unable to download webpage",
            "getaddrinfo failed",
            "name or service not known",
            "temporary failure in name resolution",
            "network is unreachable",
            "no address associated with hostname",
            "connection refused",
            "connection reset",
        ),
        "Brak połączenia z internetem. Sprawdź połączenie i spróbuj ponownie.",
    ),
    (
        ("unsupported url",),
        "Nie rozpoznaję tego linku jako filmu z YouTube.",
    ),
    (
        (
            "geo-restricted",
            "georestricted",
            "not available in your country",
            "not available in your location",
            "not made this video available",
            "blocked it in your country",
        ),
        "Film jest niedostępny w Twoim regionie.",
    ),
    (
        ("live event will begin",),
        "To jest transmisja na żywo, która jeszcze się nie zaczęła.",
    ),
    (
        ("premiere will begin",),
        "To jest premiera, która jeszcze się nie zaczęła.",
    ),
)


def map_yt_dlp_error(error_text: str) -> str:
    if not error_text:
        return _GENERIC
    lowered = error_text.lower()
    for keywords, message in _PATTERNS:
        for kw in keywords:
            if kw in lowered:
                return message
    return _GENERIC


_GENERIC = "Nie udało się pobrać filmu. Szczegóły zapisałem w pliku log."
