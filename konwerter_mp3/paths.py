from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional


def get_downloads_folder(home: Optional[Path] = None, platform: Optional[str] = None) -> Path:
    """Return the user's real Downloads folder.

    On Windows, uses SHGetKnownFolderPath so a relocated folder (OneDrive etc.)
    is honoured. Elsewhere, falls back to ``$HOME/Downloads``.
    """
    plat = platform if platform is not None else sys.platform
    if plat == "win32":
        try:
            return _shgetknownfolderpath_downloads()
        except Exception:
            pass
    base = home if home is not None else Path.home()
    return base / "Downloads"


def get_app_dir(local_appdata: Optional[Path] = None, home: Optional[Path] = None) -> Path:
    """Return %LOCALAPPDATA%\\KonwerterMP3 (or fallback) as a Path."""
    if local_appdata is None:
        env = os.environ.get("LOCALAPPDATA")
        if env:
            local_appdata = Path(env)
        else:
            base = home if home is not None else Path.home()
            local_appdata = base / "AppData" / "Local"
    return local_appdata / "KonwerterMP3"


def _shgetknownfolderpath_downloads() -> Path:  # pragma: no cover - Windows only
    import ctypes
    from ctypes import byref, windll, wintypes

    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", wintypes.DWORD),
            ("Data2", wintypes.WORD),
            ("Data3", wintypes.WORD),
            ("Data4", ctypes.c_ubyte * 8),
        ]

    FOLDERID_Downloads = GUID(
        0x374DE290,
        0x123F,
        0x4565,
        (ctypes.c_ubyte * 8)(0x91, 0x64, 0x39, 0xC4, 0x92, 0x5E, 0x46, 0x7B),
    )

    SHGetKnownFolderPath = windll.shell32.SHGetKnownFolderPath
    SHGetKnownFolderPath.argtypes = [
        ctypes.POINTER(GUID),
        wintypes.DWORD,
        wintypes.HANDLE,
        ctypes.POINTER(ctypes.c_wchar_p),
    ]
    SHGetKnownFolderPath.restype = ctypes.c_long

    path_ptr = ctypes.c_wchar_p()
    hr = SHGetKnownFolderPath(byref(FOLDERID_Downloads), 0, None, byref(path_ptr))
    if hr != 0 or not path_ptr.value:
        raise OSError(f"SHGetKnownFolderPath zwróciło {hr}")
    try:
        return Path(path_ptr.value)
    finally:
        windll.ole32.CoTaskMemFree(path_ptr)
