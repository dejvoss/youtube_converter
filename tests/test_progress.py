import pytest

from konwerter_mp3.progress import (
    ProgressAnnouncer,
    parse_download_destination,
    parse_extract_destination,
    parse_percent,
)


def test_parse_percent_integer():
    assert parse_percent("[download]  25% of  3.50MiB at 1.23MiB/s ETA 00:02") == 25.0


def test_parse_percent_float():
    assert parse_percent("[download]  12.4% of  3.50MiB") == 12.4


def test_parse_percent_no_match():
    assert parse_percent("[download] Destination: Song.webm") is None
    assert parse_percent("random line") is None


def test_parse_download_destination():
    assert parse_download_destination("[download] Destination: My Song.webm") == "My Song.webm"


def test_parse_extract_destination():
    assert (
        parse_extract_destination("[ExtractAudio] Destination: My Song.mp3")
        == "My Song.mp3"
    )


def _collect(announcer_calls):
    calls = []

    def say(msg):
        calls.append(msg)

    return say, calls


def _feed_lines(lines):
    say, calls = _collect([])
    announcer = ProgressAnnouncer(say)
    for line in lines:
        announcer.feed(line)
    return announcer, calls


def test_announcer_milestones_fire_once_each():
    lines = [
        "[download] Destination: Rick Astley - Never Gonna Give You Up.webm",
        "[download]   0.1% of  3.50MiB",
        "[download]   5.0% of  3.50MiB",
        "[download]  24.9% of  3.50MiB",
        "[download]  25.0% of  3.50MiB",
        "[download]  30.5% of  3.50MiB",
        "[download]  49.1% of  3.50MiB",
        "[download]  50.0% of  3.50MiB",
        "[download]  55.0% of  3.50MiB",
        "[download]  74.0% of  3.50MiB",
        "[download]  75.1% of  3.50MiB",
        "[download]  99.9% of  3.50MiB",
        "[download] 100% of  3.50MiB in 00:02",
        "[ExtractAudio] Destination: Rick Astley - Never Gonna Give You Up.mp3",
    ]
    announcer, calls = _feed_lines(lines)
    assert calls == [
        "Pobieram: Rick Astley - Never Gonna Give You Up.",
        "Pobrano 25 procent.",
        "Pobrano 50 procent.",
        "Pobrano 75 procent.",
        "Konwertuję do MP3.",
    ]
    assert announcer.title == "Rick Astley - Never Gonna Give You Up"
    assert announcer.mp3_filename == "Rick Astley - Never Gonna Give You Up.mp3"


def test_announcer_no_duplicate_milestones_when_percent_jumps():
    # A jump straight past 25 should still only fire the 25 milestone once.
    lines = [
        "[download] Destination: X.webm",
        "[download]  60.0% of  3.50MiB",
        "[download]  61.0% of  3.50MiB",
        "[download]  80.0% of  3.50MiB",
    ]
    _, calls = _feed_lines(lines)
    assert calls == [
        "Pobieram: X.",
        "Pobrano 25 procent.",
        "Pobrano 50 procent.",
        "Pobrano 75 procent.",
    ]


def test_announcer_does_not_announce_every_percent():
    # 1000 tiny progress lines should still produce at most a handful of calls.
    lines = ["[download] Destination: Song.webm"]
    for i in range(1000):
        pct = i / 10.0  # 0.0 .. 99.9
        lines.append(f"[download] {pct:5.1f}% of 10.0MiB")
    _, calls = _feed_lines(lines)
    # 1 title + 3 milestones = 4 announcements total
    assert len(calls) == 4


def test_announcer_handles_extract_without_destination_line():
    lines = [
        "[download] Destination: Song.webm",
        "[download]  50.0% of  3.50MiB",
        "[ExtractAudio] Extracting audio",
    ]
    _, calls = _feed_lines(lines)
    assert calls[-1] == "Konwertuję do MP3."
