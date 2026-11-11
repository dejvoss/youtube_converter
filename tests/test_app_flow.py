import io
import logging
from pathlib import Path

import pytest

from konwerter_mp3.accessibility import Announcer
from konwerter_mp3.app import run_one_download
from konwerter_mp3.downloader import YtDlpRunner
from konwerter_mp3.errors import ConverterError


class _FakeProc:
    def __init__(self, lines, rc):
        self.stdout = iter(line + "\n" for line in lines)
        self._rc = rc

    def wait(self):
        return self._rc


def _make_popen(lines, rc=0):
    def _popen(cmd, **kwargs):
        return _FakeProc(lines, rc)
    return _popen


def _make_logger():
    logger = logging.getLogger("test")
    logger.handlers.clear()
    logger.addHandler(logging.NullHandler())
    return logger


def test_run_one_download_success_announces_minimal_output(tmp_path):
    stream = io.StringIO()
    announcer = Announcer(stream=stream)
    lines = [
        "[download] Destination: Song Title.webm",
        "[download]   0.1% of 3.5MiB",
        "[download]  25.0% of 3.5MiB",
        "[download]  50.0% of 3.5MiB",
        "[download]  75.0% of 3.5MiB",
        "[download] 100% of 3.5MiB in 00:03",
        "[ExtractAudio] Destination: Song Title.mp3",
    ]
    runner = YtDlpRunner(
        Path("/x/yt-dlp.exe"),
        Path("/x/ffmpeg.exe"),
        popen=_make_popen(lines, rc=0),
    )
    run_one_download("https://youtu.be/xyz", runner, tmp_path, announcer, _make_logger())

    output_lines = [l for l in stream.getvalue().splitlines() if l]
    assert output_lines == [
        "Pobieram: Song Title.",
        "Pobrano 25 procent.",
        "Pobrano 50 procent.",
        "Pobrano 75 procent.",
        "Konwertuję do MP3.",
        "Gotowe. Zapisano plik Song Title.mp3 w folderze Pobrane.",
    ]


def test_run_one_download_failure_maps_error(tmp_path):
    stream = io.StringIO()
    announcer = Announcer(stream=stream)
    lines = [
        "[youtube] XXX: Downloading webpage",
        "ERROR: [youtube] XXX: Private video. Sign in if you've been granted access to this video",
    ]
    runner = YtDlpRunner(
        Path("/x/yt-dlp.exe"),
        Path("/x/ffmpeg.exe"),
        popen=_make_popen(lines, rc=1),
    )
    with pytest.raises(ConverterError) as exc_info:
        run_one_download("https://youtu.be/xyz", runner, tmp_path, announcer, _make_logger())
    assert "prywatny" in exc_info.value.user_message.lower()


def test_announcer_writes_one_line_per_call():
    stream = io.StringIO()
    announcer = Announcer(stream=stream)
    announcer.say("Pierwsza linia.")
    announcer.say("Druga linia.")
    assert stream.getvalue() == "Pierwsza linia.\nDruga linia.\n"
