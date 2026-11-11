from __future__ import annotations

import sys


class Announcer:
    """Prints plain, screen-reader friendly lines.

    One short sentence per line. No carriage returns, no in-place updates,
    no progress bars, no color codes. We want each announcement to be a
    single discrete line NVDA/JAWS reads once.
    """

    def __init__(self, stream=None) -> None:
        self._stream = stream if stream is not None else sys.stdout

    def say(self, text: str) -> None:
        self._stream.write(text + "\n")
        self._stream.flush()


def success_beep() -> None:
    _beep(_WINSOUND_SUCCESS)


def error_beep() -> None:
    _beep(_WINSOUND_ERROR)


_WINSOUND_SUCCESS = "MB_ICONASTERISK"
_WINSOUND_ERROR = "MB_ICONHAND"


def _beep(kind: str) -> None:
    if sys.platform != "win32":
        return
    try:
        import winsound  # type: ignore[import-not-found]
    except ImportError:
        return
    code = getattr(winsound, kind, None)
    if code is None:
        return
    try:
        winsound.MessageBeep(code)
    except Exception:
        pass
