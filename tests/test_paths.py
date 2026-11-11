from pathlib import Path

from konwerter_mp3.paths import get_app_dir, get_downloads_folder


def test_get_downloads_folder_non_windows(tmp_path):
    (tmp_path / "Downloads").mkdir()
    result = get_downloads_folder(home=tmp_path, platform="linux")
    assert result == tmp_path / "Downloads"


def test_get_downloads_folder_defaults_to_home_downloads(tmp_path):
    # Folder need not exist; function returns a path either way.
    result = get_downloads_folder(home=tmp_path, platform="darwin")
    assert result == tmp_path / "Downloads"


def test_get_app_dir_uses_local_appdata(tmp_path):
    result = get_app_dir(local_appdata=tmp_path)
    assert result == tmp_path / "KonwerterMP3"


def test_get_app_dir_fallback(tmp_path, monkeypatch):
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    result = get_app_dir(home=tmp_path)
    assert result == tmp_path / "AppData" / "Local" / "KonwerterMP3"
