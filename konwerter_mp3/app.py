from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from .accessibility import Announcer, error_beep, success_beep
from .clipboard import read_clipboard_text
from .downloader import YtDlpRunner, collect_error_lines
from .errors import ConverterError, map_yt_dlp_error
from .logger import setup_logger
from .paths import get_app_dir, get_downloads_folder
from .progress import ProgressAnnouncer
from .setup_tools import ensure_ffmpeg, ensure_yt_dlp
from .validation import is_valid_youtube_url


FORMAT_LABELS = {"mp3": "MP3", "mp4": "MP4"}
_FORMAT_CHOICES = {
    "1": "mp3", "mp3": "mp3", "m": "mp3",
    "2": "mp4", "mp4": "mp4", "f": "mp4", "film": "mp4", "wideo": "mp4",
}


def parse_format_choice(raw: str, default: str) -> Optional[str]:
    """Zwraca "mp3"/"mp4", ``default`` dla pustego wpisu, None gdy nieznany."""
    text = raw.strip().lower().lstrip(".")
    if not text:
        return default
    return _FORMAT_CHOICES.get(text)


def format_prompt(default: str) -> str:
    return (
        "Wybierz format. Wpisz 1, aby pobrać dźwięk MP3, albo 2, aby pobrać film MP4. "
        f"Sam Enter wybiera {FORMAT_LABELS[default]}."
    )


def ask_format(announcer: Announcer, default: str, read=input) -> Optional[str]:
    """Pyta o format. Zwraca None, gdy użytkownik zamknął wejście."""
    while True:
        announcer.say(format_prompt(default))
        try:
            raw = read()
        except EOFError:
            return None
        fmt = parse_format_choice(raw, default)
        if fmt:
            return fmt
        announcer.say("Nie rozumiem. Wpisz 1 albo 2.")
        error_beep()


def run_one_download(
    url: str,
    runner: YtDlpRunner,
    downloads_dir: Path,
    announcer: Announcer,
    logger,
    fmt: str = "mp3",
) -> None:
    tracker = ProgressAnnouncer(announcer.say, fmt=fmt)
    all_lines: list[str] = []

    def on_line(line: str) -> None:
        all_lines.append(line)
        logger.debug(line)
        tracker.feed(line)

    rc, _ = runner.download(url, downloads_dir, on_line, fmt=fmt)
    if rc != 0:
        err_text = collect_error_lines(all_lines) or "\n".join(all_lines[-20:])
        raise ConverterError(map_yt_dlp_error(err_text), detail=err_text)

    name = tracker.output_filename or (
        f"{tracker.title}.{fmt}" if tracker.title else f"plik.{fmt}"
    )
    announcer.say(f"Gotowe. Zapisano plik {name} w folderze Pobrane.")


def _wait_before_exit() -> None:
    """Nie zamykaj od razu okna, żeby dało się przeczytać komunikat."""
    try:
        input("Naciśnij Enter, aby zamknąć.")
    except (EOFError, KeyboardInterrupt):
        pass


def main(argv: Optional[list[str]] = None) -> int:
    app_dir = get_app_dir()
    app_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_logger(app_dir / "log.txt")
    _enable_crash_log(app_dir / "crash.txt")
    try:
        return _main(app_dir, logger)
    except Exception:
        logger.exception("Nieoczekiwany błąd przy uruchomieniu")
        Announcer().say(
            f"Wystąpił nieoczekiwany błąd. Szczegóły są w pliku {app_dir / 'log.txt'}"
        )
        error_beep()
        _wait_before_exit()
        return 3


_crash_file = None


def _enable_crash_log(path: Path) -> None:
    """Zapisuje ślad nawet przy twardym crashu (np. błąd w ctypes)."""
    global _crash_file
    try:
        import faulthandler

        _crash_file = open(path, "a", encoding="utf-8")
        faulthandler.enable(_crash_file)
    except Exception:
        pass


def _main(app_dir: Path, logger) -> int:
    announcer = Announcer()

    announcer.say("Konwerter YouTube do MP3 i MP4.")

    try:
        first_run = not (app_dir / "yt-dlp.exe").exists() or not (app_dir / "ffmpeg.exe").exists()
        if first_run:
            announcer.say("Pierwsze uruchomienie. Pobieram potrzebne pliki, to potrwa około minuty.")
        yt_dlp_path = ensure_yt_dlp(app_dir)
        ffmpeg_path, _ = ensure_ffmpeg(app_dir)
        if first_run:
            announcer.say("Pliki pobrane. Program jest gotowy do użycia.")
    except Exception as exc:
        logger.exception("Setup nie powiódł się")
        announcer.say(
            "Nie udało się pobrać potrzebnych plików. Sprawdź połączenie z internetem "
            "i czy antywirus nie blokuje programu."
        )
        announcer.say(f"Szczegóły są w pliku {app_dir / 'log.txt'}")
        error_beep()
        _wait_before_exit()
        return 2

    runner = YtDlpRunner(yt_dlp_path, ffmpeg_path)
    if not first_run:
        try:
            runner.self_update()
        except Exception:
            logger.exception("Aktualizacja yt-dlp nie powiodła się")

    downloads_dir = get_downloads_folder()

    last_format = "mp3"
    pending_from_clipboard: Optional[str] = None
    clip = read_clipboard_text()
    if clip and is_valid_youtube_url(clip.strip()):
        pending_from_clipboard = clip.strip()
        announcer.say("W schowku jest link do YouTube. Naciśnij Enter, aby go pobrać, albo wklej inny.")
    else:
        announcer.say("Wklej link i naciśnij Enter. Aby zakończyć, naciśnij Enter bez wpisywania niczego.")

    while True:
        try:
            raw = input().strip()
        except EOFError:
            break
        except KeyboardInterrupt:
            announcer.say("Przerwano.")
            return 1

        if not raw and pending_from_clipboard:
            url = pending_from_clipboard
        elif not raw:
            break
        else:
            url = raw

        pending_from_clipboard = None

        if not is_valid_youtube_url(url):
            announcer.say("To nie wygląda na link do YouTube. Wklej link zaczynający się od https.")
            error_beep()
            announcer.say("Wklej kolejny link i naciśnij Enter. Aby zakończyć, naciśnij Enter bez wpisywania niczego.")
            continue

        try:
            fmt = ask_format(announcer, last_format)
        except KeyboardInterrupt:
            announcer.say("Przerwano.")
            return 1
        if fmt is None:
            break
        last_format = fmt

        try:
            run_one_download(url, runner, downloads_dir, announcer, logger, fmt=fmt)
            success_beep()
        except ConverterError as exc:
            logger.error("Konwersja nie powiodła się: %s", exc.detail)
            announcer.say(exc.user_message)
            error_beep()
        except Exception:
            logger.exception("Nieoczekiwany błąd")
            announcer.say("Wystąpił nieoczekiwany błąd. Szczegóły są w pliku log.")
            error_beep()

        announcer.say("Wklej kolejny link i naciśnij Enter. Aby zakończyć, naciśnij Enter bez wpisywania niczego.")

    announcer.say("Do widzenia.")
    return 0
