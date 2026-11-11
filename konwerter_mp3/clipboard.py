from __future__ import annotations

import sys
from typing import Optional


def read_clipboard_text() -> Optional[str]:
    """Return the current Windows clipboard as text, or None if unavailable.

    On non-Windows platforms, always returns None (used in tests).
    """
    if sys.platform != "win32":
        return None
    try:  # pragma: no cover - Windows only
        import ctypes
        from ctypes import windll

        CF_UNICODETEXT = 13
        user32 = windll.user32
        kernel32 = windll.kernel32

        if not user32.OpenClipboard(None):
            return None
        try:
            handle = user32.GetClipboardData(CF_UNICODETEXT)
            if not handle:
                return None
            locked = kernel32.GlobalLock(handle)
            if not locked:
                return None
            try:
                value = ctypes.c_wchar_p(locked).value
                return value
            finally:
                kernel32.GlobalUnlock(handle)
        finally:
            user32.CloseClipboard()
    except Exception:
        return None
