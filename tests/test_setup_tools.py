import zipfile

import pytest

from konwerter_mp3 import setup_tools
from konwerter_mp3.setup_tools import _download, ensure_yt_dlp, extract_ffmpeg_binaries

BIG = b"x" * (setup_tools._MIN_SIZE + 1)


def _ok(url, dest):
    dest.write_bytes(BIG)


def _fail(url, dest):
    raise OSError("SSL: CERTIFICATE_VERIFY_FAILED")


def _partial_then_fail(url, dest):
    dest.write_bytes(b"half")
    raise OSError("connection reset")


def test_download_falls_back_to_next_method(tmp_path):
    dest = tmp_path / "yt-dlp.exe"
    _download("https://x", dest, methods=[_fail, _ok])
    assert dest.read_bytes() == BIG
    assert not (tmp_path / "yt-dlp.exe.part").exists()


def test_download_all_fail_leaves_no_file(tmp_path):
    dest = tmp_path / "yt-dlp.exe"
    with pytest.raises(IOError) as e:
        _download("https://x", dest, methods=[_partial_then_fail, _fail])
    assert not dest.exists()
    assert not (tmp_path / "yt-dlp.exe.part").exists()
    assert "CERTIFICATE_VERIFY_FAILED" in str(e.value)


def test_download_rejects_too_small_file(tmp_path):
    dest = tmp_path / "f"
    with pytest.raises(IOError):
        _download("https://x", dest, methods=[lambda u, d: d.write_bytes(b"<html>")])
    assert not dest.exists()


def test_ensure_yt_dlp_redownloads_truncated_file(tmp_path):
    (tmp_path / "yt-dlp.exe").write_bytes(b"broken")
    calls = []
    ensure_yt_dlp(tmp_path, download=lambda u, d: (calls.append(u), d.write_bytes(BIG)))
    assert calls


def test_extract_ffmpeg_requires_both_binaries(tmp_path):
    z = tmp_path / "a.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("ffmpeg-x/bin/ffmpeg.exe", b"1")
    with pytest.raises(IOError):
        extract_ffmpeg_binaries(z, tmp_path)


def test_ssl_contexts_prefers_windows_store():
    names = [n for n, _ in setup_tools._ssl_contexts()]
    assert names[0] == "certyfikaty Windows"
    assert names[-1] == "domyślne Pythona"
