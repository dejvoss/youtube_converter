from __future__ import annotations

import re
from pathlib import PurePath
from typing import Callable, Optional

_PERCENT_RE = re.compile(r"^\[download\]\s+(\d+(?:\.\d+)?)%")
_DEST_RE = re.compile(r"^\[download\]\s+Destination:\s+(.+?)\s*$")
_EXTRACT_RE = re.compile(r"^\[ExtractAudio\]")
_FINAL_DEST_RE = re.compile(r"^\[ExtractAudio\]\s+Destination:\s+(.+?)\s*$")
_MERGER_RE = re.compile(r'^\[Merger\]\s+Merging formats into\s+"(.+)"\s*$')
_FORMAT_SUFFIX_RE = re.compile(r"\.f[0-9a-zA-Z-]+$")


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


def parse_merger_destination(line: str) -> Optional[str]:
    m = _MERGER_RE.match(line)
    if m:
        return m.group(1).strip()
    return None


def clean_title(stem: str) -> str:
    """Usuwa dopisek formatu yt-dlp, np. "Tytuł.f137" -> "Tytuł"."""
    return _FORMAT_SUFFIX_RE.sub("", stem)


def is_extract_audio(line: str) -> bool:
    return bool(_EXTRACT_RE.match(line))


class ProgressAnnouncer:
    """Turns yt-dlp --newline output into spoken-friendly announcements.

    Fires only on milestones (25/50/75), on download start,
    and on conversion start. 100% is implied by completion message.
    """

    MILESTONES = (25, 50, 75)

    def __init__(self, announce: Callable[[str], None], fmt: str = "mp3") -> None:
        self._announce = announce
        self._fmt = fmt
        self._reported: set[int] = set()
        self._title: Optional[str] = None
        self._output_name: Optional[str] = None
        self._extract_announced = False
        self._merge_announced = False

    @property
    def title(self) -> Optional[str]:
        return self._title

    @property
    def output_filename(self) -> Optional[str]:
        return self._output_name

    # Zgodność wstecz.
    mp3_filename = output_filename

    def feed(self, line: str) -> None:
        dest = parse_download_destination(line)
        if dest:
            if self._title is None:
                self._title = clean_title(PurePath(dest).stem)
                self._announce(f"Pobieram: {self._title}.")
            if self._fmt == "mp4" and self._output_name is None:
                name = PurePath(dest).name
                if PurePath(name).suffix.lower() == ".mp4" and clean_title(PurePath(name).stem) == PurePath(name).stem:
                    self._output_name = name
            return

        merged = parse_merger_destination(line)
        if merged:
            self._output_name = PurePath(merged.replace("\\", "/")).name
            if not self._merge_announced:
                self._merge_announced = True
                self._announce("Łączę obraz z dźwiękiem.")
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
            self._output_name = PurePath(extract_dest).name
            if not self._extract_announced:
                self._extract_announced = True
                self._announce("Konwertuję do MP3.")
            return

        if is_extract_audio(line) and not self._extract_announced:
            self._extract_announced = True
            self._announce("Konwertuję do MP3.")
