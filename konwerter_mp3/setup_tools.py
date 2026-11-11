from __future__ import annotations

import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable, Optional

YT_DLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
FFMPEG_ZIP_URL = (
    "https://github.com/yt-dlp/FFmpeg-Builds/releases/latest/download/"
    "ffmpeg-master-latest-win64-gpl.zip"
)


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "KonwerterMP3/1.0"})
    with urllib.request.urlopen(req) as resp, open(dest, "wb") as out:
        shutil.copyfileobj(resp, out)


def ensure_yt_dlp(
    target_dir: Path,
    download: Callable[[str, Path], None] = _download,
) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    exe = target_dir / "yt-dlp.exe"
    if not exe.exists():
        download(YT_DLP_URL, exe)
    return exe


def ensure_ffmpeg(
    target_dir: Path,
    download: Callable[[str, Path], None] = _download,
) -> tuple[Path, Path]:
    target_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg = target_dir / "ffmpeg.exe"
    ffprobe = target_dir / "ffprobe.exe"
    if ffmpeg.exists() and ffprobe.exists():
        return ffmpeg, ffprobe

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tf:
        tmp = Path(tf.name)
    try:
        download(FFMPEG_ZIP_URL, tmp)
        extract_ffmpeg_binaries(tmp, target_dir)
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass
    return ffmpeg, ffprobe


def extract_ffmpeg_binaries(zip_path: Path, target_dir: Path) -> None:
    wanted = {"ffmpeg.exe", "ffprobe.exe"}
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            base = name.rsplit("/", 1)[-1].lower()
            if base in wanted:
                dest = target_dir / base
                with z.open(name) as src, open(dest, "wb") as out:
                    shutil.copyfileobj(src, out)
