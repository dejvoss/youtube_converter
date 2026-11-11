from __future__ import annotations

import logging
import os
import shutil
import subprocess
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


_USER_AGENT = "KonwerterMP3/1.0"
_TIMEOUT = 300
_MIN_SIZE = 100_000  # prawdziwe pliki mają kilka-kilkadziesiąt MB


def _download_urllib(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp, open(dest, "wb") as out:
        shutil.copyfileobj(resp, out)


def _no_window() -> int:
    return getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _download_curl(url: str, dest: Path) -> None:
    # curl.exe jest wbudowany w Windows 10/11 i używa certyfikatów systemu
    # (Schannel), więc działa tam, gdzie Python ma problem z SSL.
    system32 = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"
    curl = system32 / "curl.exe"
    exe = str(curl) if curl.exists() else (shutil.which("curl") or "curl")
    subprocess.run(
        [exe, "-fsSL", "--retry", "3", "-A", _USER_AGENT, "-o", str(dest), url],
        check=True,
        timeout=_TIMEOUT,
        creationflags=_no_window(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )


def _download_powershell(url: str, dest: Path) -> None:
    script = (
        "$ProgressPreference='SilentlyContinue';"
        "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;"
        f"Invoke-WebRequest -UseBasicParsing -Uri '{url}' -OutFile '{dest}'"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        check=True,
        timeout=_TIMEOUT,
        creationflags=_no_window(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )


_METHODS: list[Callable[[str, Path], None]] = [
    _download_urllib,
    _download_curl,
    _download_powershell,
]


def _download(url: str, dest: Path, methods: Optional[list] = None) -> None:
    """Pobiera plik, próbując kolejno kilku metod.

    Zapisuje najpierw do pliku .part i zmienia nazwę dopiero po sukcesie,
    żeby przerwane pobieranie nie zostawiło uszkodzonego pliku.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    errors: list[str] = []
    for method in methods if methods is not None else _METHODS:
        try:
            part.unlink(missing_ok=True)
            method(url, part)
            if not part.exists() or part.stat().st_size < _MIN_SIZE:
                raise IOError("pobrany plik jest pusty lub za mały")
            os.replace(part, dest)
            return
        except Exception as exc:  # próbujemy następnej metody
            detail = exc
            if isinstance(exc, subprocess.CalledProcessError) and exc.stderr:
                detail = f"{exc} | {exc.stderr.decode(errors='replace').strip()}"
            errors.append(f"{getattr(method, '__name__', method)}: {detail}")
            logging.getLogger("konwerter_mp3").warning(
                "Pobieranie %s metodą %s nie powiodło się: %s",
                url, getattr(method, "__name__", method), detail,
            )
    try:
        part.unlink(missing_ok=True)
    except OSError:
        pass
    raise IOError("Nie udało się pobrać " + url + ":\n" + "\n".join(errors))


def ensure_yt_dlp(
    target_dir: Path,
    download: Callable[[str, Path], None] = _download,
) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    exe = target_dir / "yt-dlp.exe"
    if not exe.exists() or exe.stat().st_size < _MIN_SIZE:
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
    found: set[str] = set()
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            base = name.rsplit("/", 1)[-1].lower()
            if base in wanted:
                dest = target_dir / base
                with z.open(name) as src, open(dest, "wb") as out:
                    shutil.copyfileobj(src, out)
                found.add(base)
    missing = wanted - found
    if missing:
        raise IOError("W archiwum FFmpeg brakuje: " + ", ".join(sorted(missing)))
