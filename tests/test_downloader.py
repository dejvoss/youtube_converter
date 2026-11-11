from pathlib import Path

from konwerter_mp3.downloader import (
    YtDlpRunner,
    build_yt_dlp_command,
    collect_error_lines,
)


def test_build_yt_dlp_command_has_all_required_flags():
    cmd = build_yt_dlp_command(
        yt_dlp_path=Path("/tmp/yt-dlp.exe"),
        ffmpeg_path=Path("/tmp/ffmpeg.exe"),
        url="https://youtu.be/xyz",
        downloads_dir=Path("/tmp/dl"),
    )
    assert cmd[0] == "/tmp/yt-dlp.exe"
    assert "-x" in cmd
    assert cmd[cmd.index("--audio-format") + 1] == "mp3"
    assert cmd[cmd.index("--audio-quality") + 1] == "0"
    assert "--no-playlist" in cmd
    assert "--embed-metadata" in cmd
    assert cmd[cmd.index("--ffmpeg-location") + 1] == "/tmp/ffmpeg.exe"
    assert cmd[cmd.index("-o") + 1] == "%(title)s.%(ext)s"
    assert cmd[cmd.index("-P") + 1] == "/tmp/dl"
    assert "--newline" in cmd
    assert "--no-colors" in cmd
    assert cmd[-1] == "https://youtu.be/xyz"


def test_collect_error_lines_filters_only_error_lines():
    lines = [
        "[download] 100% of ...",
        "ERROR: Something bad",
        "[download] Destination: x",
        "yt-dlp: error: invalid url",
    ]
    text = collect_error_lines(lines)
    assert "ERROR: Something bad" in text
    assert "yt-dlp: error: invalid url" in text
    assert "[download]" not in text


class _FakeProc:
    def __init__(self, lines, rc):
        self._lines = list(lines)
        self.stdout = iter(line + "\n" for line in self._lines)
        self._rc = rc

    def wait(self):
        return self._rc


def _fake_popen_factory(lines, rc=0, capture=None):
    def _popen(cmd, **kwargs):
        if capture is not None:
            capture.append(cmd)
        return _FakeProc(lines, rc)
    return _popen


def test_runner_streams_lines_and_returns_rc():
    captured_cmd = []
    popen = _fake_popen_factory(
        [
            "[download] Destination: Song.webm",
            "[download]  50.0% of 3.5MiB",
            "[download] 100% of 3.5MiB",
            "[ExtractAudio] Destination: Song.mp3",
        ],
        rc=0,
        capture=captured_cmd,
    )
    runner = YtDlpRunner(Path("/x/yt-dlp.exe"), Path("/x/ffmpeg.exe"), popen=popen)
    collected = []
    rc, lines = runner.download(
        "https://youtu.be/xyz",
        Path("/dl"),
        on_line=collected.append,
    )
    assert rc == 0
    assert "[download]  50.0% of 3.5MiB" in collected
    assert len(collected) == 4
    assert captured_cmd[0][0] == "/x/yt-dlp.exe"
    assert captured_cmd[0][-1] == "https://youtu.be/xyz"


def test_runner_reports_nonzero_rc():
    popen = _fake_popen_factory(
        [
            "ERROR: [youtube] XXX: Private video. Sign in",
        ],
        rc=1,
    )
    runner = YtDlpRunner(Path("/x/yt-dlp.exe"), Path("/x/ffmpeg.exe"), popen=popen)
    rc, lines = runner.download(
        "https://youtu.be/xyz",
        Path("/dl"),
        on_line=lambda _l: None,
    )
    assert rc == 1
    assert lines == ["ERROR: [youtube] XXX: Private video. Sign in"]
