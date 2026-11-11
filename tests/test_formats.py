import io
import logging
from pathlib import Path

import pytest

from konwerter_mp3.accessibility import Announcer
from konwerter_mp3.app import ask_format, parse_format_choice, run_one_download
from konwerter_mp3.downloader import YtDlpRunner, build_yt_dlp_command
from konwerter_mp3.progress import ProgressAnnouncer, clean_title


def _cmd(fmt):
    return build_yt_dlp_command(Path("y"), Path("f"), "https://youtu.be/x", Path("d"), fmt)


def test_mp4_command_merges_to_mp4_without_audio_extraction():
    cmd = _cmd("mp4")
    assert "-x" not in cmd
    assert cmd[cmd.index("--merge-output-format") + 1] == "mp4"
    assert "h264" in cmd[cmd.index("-S") + 1]
    assert "--no-playlist" in cmd and cmd[-1] == "https://youtu.be/x"


def test_mp3_is_default():
    cmd = build_yt_dlp_command(Path("y"), Path("f"), "u", Path("d"))
    assert cmd[cmd.index("--audio-format") + 1] == "mp3"


def test_unknown_format_rejected():
    with pytest.raises(ValueError):
        _cmd("avi")


@pytest.mark.parametrize("raw,expected", [
    ("", "mp3"), ("1", "mp3"), ("MP3", "mp3"), (" 2 ", "mp4"),
    ("mp4", "mp4"), (".mp4", "mp4"), ("film", "mp4"), ("3", None), ("xyz", None),
])
def test_parse_format_choice(raw, expected):
    assert parse_format_choice(raw, "mp3") == expected


def test_empty_choice_uses_last_format():
    assert parse_format_choice("", "mp4") == "mp4"


def test_ask_format_repeats_on_bad_input():
    out = io.StringIO()
    answers = iter(["zle", "2"])
    fmt = ask_format(Announcer(stream=out), "mp3", read=lambda: next(answers))
    assert fmt == "mp4"
    assert "Nie rozumiem. Wpisz 1 albo 2." in out.getvalue()
    assert out.getvalue().count("Wybierz format.") == 2


def test_clean_title_strips_format_id():
    assert clean_title("Mój film.f137") == "Mój film"
    assert clean_title("Wersja 1.0") == "Wersja 1.0"


class _Proc:
    def __init__(self, lines):
        self.stdout = iter(l + "\n" for l in lines)

    def wait(self):
        return 0


def test_mp4_download_announcements(tmp_path):
    lines = [
        "[download] Destination: C:\\Users\\a\\Downloads\\Mój film.f137.mp4",
        "[download]  30.0% of 50MiB",
        "[download] 100% of 50MiB",
        "[download] Destination: C:\\Users\\a\\Downloads\\Mój film.f140.m4a",
        "[download]  50.0% of 3MiB",
        '[Merger] Merging formats into "C:\\Users\\a\\Downloads\\Mój film.mp4"',
    ]
    runner = YtDlpRunner(Path("y"), Path("f"), popen=lambda cmd, **k: _Proc(lines))
    out = io.StringIO()
    run_one_download("https://youtu.be/x", runner, tmp_path, Announcer(stream=out),
                     logging.getLogger("t"), fmt="mp4")
    said = [l for l in out.getvalue().splitlines() if l]
    assert said[0].endswith("Mój film.")
    assert "Pobrano 25 procent." in said
    assert "Łączę obraz z dźwiękiem." in said
    assert said[-1] == "Gotowe. Zapisano plik Mój film.mp4 w folderze Pobrane."
    assert not any("MP3" in l for l in said)


def test_mp4_single_file_without_merge():
    t = ProgressAnnouncer(lambda _s: None, fmt="mp4")
    t.feed("[download] Destination: /d/Klip.mp4")
    assert t.output_filename == "Klip.mp4"
