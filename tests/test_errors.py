import pytest

from konwerter_mp3.errors import ConverterError, map_yt_dlp_error


@pytest.mark.parametrize(
    "fragment,expected_substring",
    [
        ("ERROR: [youtube] XXX: Private video. Sign in", "prywatny"),
        ("ERROR: [youtube] XXX: Video unavailable", "usunięty lub jest niedostępny"),
        (
            "ERROR: [youtube] XXX: This video has been removed by the uploader",
            "usunięty lub jest niedostępny",
        ),
        (
            "ERROR: [youtube] XXX: Sign in to confirm your age. This video may be inappropriate",
            "ograniczenie wieku",
        ),
        ("ERROR: [youtube] XXX: Join this channel for members-only content", "członków"),
        (
            "ERROR: [youtube] XXX: This video contains content from UMG, who has blocked it on copyright grounds",
            "praw autorskich",
        ),
        (
            "ERROR: [generic] XXX: Unable to download webpage: <urlopen error [Errno -3] Temporary failure in name resolution>",
            "połączenia z internetem",
        ),
        (
            "ERROR: [generic] XXX: Unable to download webpage: getaddrinfo failed",
            "połączenia z internetem",
        ),
        ("ERROR: Unsupported URL: https://example.com/foo", "nie rozpoznaję"),
        (
            "ERROR: [youtube] XXX: The uploader has not made this video available in your country",
            "regionie",
        ),
    ],
)
def test_error_mapping(fragment, expected_substring):
    result = map_yt_dlp_error(fragment)
    assert expected_substring.lower() in result.lower()


def test_error_mapping_generic_fallback():
    result = map_yt_dlp_error("ERROR: something weird happened")
    assert "nie udało się" in result.lower()
    assert "log" in result.lower()


def test_error_mapping_empty():
    result = map_yt_dlp_error("")
    assert "nie udało się" in result.lower()


def test_converter_error_carries_user_message():
    err = ConverterError("Komunikat dla użytkownika", detail="raw traceback")
    assert err.user_message == "Komunikat dla użytkownika"
    assert err.detail == "raw traceback"
    assert str(err) == "Komunikat dla użytkownika"
