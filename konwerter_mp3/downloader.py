from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable, Iterable, List, Sequence


FORMATS = ("mp3", "mp4")


def _format_args(fmt: str) -> List[str]:
    if fmt == "mp3":
        return ["-x", "--audio-format", "mp3", "--audio-quality", "0"]
    if fmt == "mp4":
        # H.264 + AAC w kontenerze MP4 odtworzy każdy odtwarzacz w Windows.
        return [
            "-f", "bv*+ba/b",
            "-S", "vcodec:h264,res,acodec:m4a",
            "--merge-output-format", "mp4",
        ]
    raise ValueError(f"Nieznany format: {fmt}")


def build_yt_dlp_command(
    yt_dlp_path: Path,
    ffmpeg_path: Path,
    url: str,
    downloads_dir: Path,
    fmt: str = "mp3",
) -> List[str]:
    """Build the yt-dlp argv.

    ``ffmpeg_path`` is the folder (or file) containing ffmpeg.exe/ffprobe.exe.
    yt-dlp's --ffmpeg-location accepts either a directory or a file path.
    ``fmt`` is ``"mp3"`` (audio only) or ``"mp4"`` (video).
    """
    return [
        str(yt_dlp_path),
        *_format_args(fmt),
        "--no-playlist",
        "--embed-metadata",
        "--ffmpeg-location", str(ffmpeg_path),
        "-o", "%(title)s.%(ext)s",
        "-P", str(downloads_dir),
        "--newline",
        "--no-colors",
        url,
    ]


class YtDlpRunner:
    """Runs yt-dlp as a subprocess and streams its stdout line-by-line.

    ``popen`` is injectable so tests can run without a real yt-dlp binary.
    """

    def __init__(
        self,
        yt_dlp_path: Path,
        ffmpeg_path: Path,
        popen: Callable[..., subprocess.Popen] = subprocess.Popen,
    ) -> None:
        self.yt_dlp_path = Path(yt_dlp_path)
        self.ffmpeg_path = Path(ffmpeg_path)
        self._popen = popen

    def build_command(self, url: str, downloads_dir: Path, fmt: str = "mp3") -> List[str]:
        return build_yt_dlp_command(self.yt_dlp_path, self.ffmpeg_path, url, downloads_dir, fmt)

    def download(
        self,
        url: str,
        downloads_dir: Path,
        on_line: Callable[[str], None],
        fmt: str = "mp3",
    ) -> tuple[int, List[str]]:
        cmd = self.build_command(url, downloads_dir, fmt)
        proc = self._popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        lines: List[str] = []
        try:
            assert proc.stdout is not None
            for raw in proc.stdout:
                line = raw.rstrip("\r\n")
                lines.append(line)
                on_line(line)
        finally:
            rc = proc.wait()
        return rc, lines

    def self_update(self) -> tuple[int, List[str]]:
        cmd = [str(self.yt_dlp_path), "-U"]
        proc = self._popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        lines: List[str] = []
        try:
            assert proc.stdout is not None
            for raw in proc.stdout:
                lines.append(raw.rstrip("\r\n"))
        finally:
            rc = proc.wait()
        return rc, lines


def collect_error_lines(lines: Iterable[str]) -> str:
    out: List[str] = []
    for line in lines:
        if line.startswith("ERROR:") or line.startswith("yt-dlp: error:"):
            out.append(line)
    return "\n".join(out)
