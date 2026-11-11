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


def run_one_download(
    url: str,
    runner: YtDlpRunner,
    downloads_dir: Path,
    announcer: Announcer,
    logger,
) -> None:
    tracker = ProgressAnnouncer(announcer.say)
    all_lines: list[str] = []

    def on_line(line: str) -> None:
        all_lines.append(line)
        logger.debug(line)
        tracker.feed(line)

    rc, _ = runner.download(url, downloads_dir, on_line)
    if rc != 0:
        err_text = collect_error_lines(all_lines) or "\n".join(all_lines[-20:])
        raise ConverterError(map_yt_dlp_error(err_text), detail=err_text)

    name = tracker.mp3_filename or (
        f"{tracker.title}.mp3" if tracker.title else "plik.mp3"
    )
    announcer.say(f"Gotowe. Zapisano plik {name} w folderze Pobrane.")


def _wait_before_exit() -> None:
    """Nie zamykaj od razu okna, żeby dało się przeczytać komunikat."""
    try:
        input("Naciśnij Enter, aby zamknąć.")
    except (EOFError, KeyboardInterrupt):
        pass


def main(argv: Optional[list[str]] = None) -> int:
    announcer = Announcer()
    app_dir = get_app_dir()
    app_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_logger(app_dir / "log.txt")

    announcer.say("Konwerter YouTube do MP3.")

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
            run_one_download(url, runner, downloads_dir, announcer, logger)
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
