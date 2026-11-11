from __future__ import annotations

import re
from pathlib import PurePath
from typing import Callable, Optional

_PERCENT_RE = re.compile(r"^\[download\]\s+(\d+(?:\.\d+)?)%")
_DEST_RE = re.compile(r"^\[download\]\s+Destination:\s+(.+?)\s*$")
_EXTRACT_RE = re.compile(r"^\[ExtractAudio\]")
_FINAL_DEST_RE = re.compile(r"^\[ExtractAudio\]\s+Destination:\s+(.+?)\s*$")


def parse_percent(line: str) -> Optional[float]:
    m = _PERCENT_RE.match(line)
    if m:
        return float(m.group(1))
    return None


def parse_download_destination(line: str) -> Optional[str]:
    m = _DEST_RE.match(line)
    if m:
        return m.group(1).strip()
    return None


def parse_extract_destination(line: str) -> Optional[str]:
    m = _FINAL_DEST_RE.match(line)
    if m:
        return m.group(1).strip()
    return None


def is_extract_audio(line: str) -> bool:
    return bool(_EXTRACT_RE.match(line))


class ProgressAnnouncer:
    """Turns yt-dlp --newline output into spoken-friendly announcements.

    Fires only on milestones (25/50/75), on download start,
    and on conversion start. 100% is implied by completion message.
    """

    MILESTONES = (25, 50, 75)

    def __init__(self, announce: Callable[[str], None]) -> None:
        self._announce = announce
        self._reported: set[int] = set()
        self._title: Optional[str] = None
        self._mp3_name: Optional[str] = None
        self._extract_announced = False

    @property
    def title(self) -> Optional[str]:
        return self._title

    @property
    def mp3_filename(self) -> Optional[str]:
        return self._mp3_name

    def feed(self, line: str) -> None:
        if self._title is None:
            dest = parse_download_destination(line)
            if dest:
                self._title = PurePath(dest).stem
                self._announce(f"Pobieram: {self._title}.")
                return

        pct = parse_percent(line)
        if pct is not None:
            for milestone in self.MILESTONES:
                if pct >= milestone and milestone not in self._reported:
                    self._reported.add(milestone)
                    self._announce(f"Pobrano {milestone} procent.")
            return

        extract_dest = parse_extract_destination(line)
        if extract_dest:
            self._mp3_name = PurePath(extract_dest).name
            if not self._extract_announced:
                self._extract_announced = True
                self._announce("Konwertuję do MP3.")
            return

        if is_extract_audio(line) and not self._extract_announced:
            self._extract_announced = True
            self._announce("Konwertuję do MP3.")
