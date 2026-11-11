import pytest

from konwerter_mp3.validation import is_valid_youtube_url


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
        "http://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://music.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/abcdefghijk",
        "https://www.youtube.com/live/abcdefghijk",
        "https://www.youtube.com/embed/abcdefghijk",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PL123&index=1",
        "  https://youtu.be/dQw4w9WgXcQ  ",
    ],
)
def test_valid_urls(url):
    assert is_valid_youtube_url(url) is True


@pytest.mark.parametrize(
    "url",
    [
        "",
        None,
        "not a url",
        "ftp://youtube.com/watch?v=xyz",
        "https://vimeo.com/123456",
        "https://youtube.evil.com/watch?v=xyz",
        "https://evil.com/youtube.com",
        "https://www.youtube.com/",
        "https://www.youtube.com/channel/UCxyz",
        "https://youtu.be/",
        "https://youtu.be",
        "javascript:alert(1)",
        "https://www.youtube.com/watch",
        "https://www.youtube.com/watch?list=PL123",
    ],
)
def test_invalid_urls(url):
    assert is_valid_youtube_url(url) is False
