from __future__ import annotations

import logging
import os
import shutil
import ssl
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


def _ssl_contexts() -> list:
    """Konteksty SSL do wypróbowania, od najlepszego.

    truststore korzysta bezpośrednio z magazynu certyfikatów Windows
    (tak jak przeglądarka), więc działa także wtedy, gdy wbudowana lista
    certyfikatów Pythona nie wystarcza (CERTIFICATE_VERIFY_FAILED).
    """
    contexts = []
    try:
        import truststore

        contexts.append(("certyfikaty Windows", truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)))
    except Exception:
        pass
    try:
        import certifi

        contexts.append(("certifi", ssl.create_default_context(cafile=certifi.where())))
    except Exception:
        pass
    contexts.append(("domyślne Pythona", ssl.create_default_context()))
    return contexts


def _download_urllib(url: str, dest: Path, context: Optional[ssl.SSLContext] = None) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=_TIMEOUT, context=context) as resp, open(dest, "wb") as out:
        shutil.copyfileobj(resp, out)


def _methods() -> list:
    methods = []
    for name, ctx in _ssl_contexts():
        def method(url: str, dest: Path, _ctx=ctx) -> None:
            _download_urllib(url, dest, _ctx)

        method.__name__ = f"urllib ({name})"
        methods.append(method)
    return methods


def _download(url: str, dest: Path, methods: Optional[list] = None) -> None:
    """Pobiera plik, próbując kolejno kilku metod.

    Zapisuje najpierw do pliku .part i zmienia nazwę dopiero po sukcesie,
    żeby przerwane pobieranie nie zostawiło uszkodzonego pliku.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    errors: list[str] = []
    for method in methods if methods is not None else _methods():
        try:
            part.unlink(missing_ok=True)
            method(url, part)
            if not part.exists() or part.stat().st_size < _MIN_SIZE:
                raise IOError("pobrany plik jest pusty lub za mały")
            os.replace(part, dest)
            return
        except Exception as exc:  # próbujemy następnej metody
            detail = exc
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
