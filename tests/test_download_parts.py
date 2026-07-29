#!/usr/bin/env python3
"""Host test for the multi-part download/merge logic in src/download_log.py.

Hermetic: it points ISPARO_DATA_DIR at a temp dir and stubs out the network
``download_url`` with a fake that writes deterministic part files, then drives the
real ``download`` -> ``download_parts`` -> ``merge_parts`` flow. So it checks the
orchestration and the concatenation (the genuinely new code) without downloading
the real ~40 GB archive. The actual streamed download is covered by
test_download_log.py.

Run via the VSCode launch config, or directly:
    python3 tests/test_download_parts.py
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="isparo_dlparts_test_")
os.environ["ISPARO_DATA_DIR"] = _TMP

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

import download_log as dl  # noqa: E402

MERGED_NAME = "20250611_Vulcano_LongTraverse.tar.gz"
PART_URLS = [f"https://example/{MERGED_NAME}.part{i:02d}/content" for i in range(1, 4)]
ENTRY = {"parts": PART_URLS, "archive_name": MERGED_NAME}

_failures = []
_download_calls = []


def check(cond, msg):
    print(("PASS: " if cond else "FAIL: ") + msg)
    if not cond:
        _failures.append(msg)


def fake_download_url(url, dest):
    """Stand-in for the real streamed download: write deterministic bytes once."""
    _download_calls.append(url)
    if not dest.exists():  # mimic the real "skip if already complete" behaviour
        dest.write_bytes((f"[{dest.name}]").encode() * 500)
    return dest


def expected_merged_bytes():
    parts = [dl.DOWNLOAD_DIR / dl.filename_from_url(u) for u in PART_URLS]
    return b"".join(p.read_bytes() for p in parts)


def main():
    dl.download_url = fake_download_url  # patch out the network
    merged = dl.DOWNLOAD_DIR / MERGED_NAME

    # First run: all parts "downloaded", then concatenated in order.
    dl.download("vulcano_long_traverse_2025", ENTRY)
    check(len(_download_calls) == 3, f"all 3 parts fetched (got {len(_download_calls)})")
    check(merged.is_file(), f"merged archive created: {merged.name}")
    check(merged.read_bytes() == expected_merged_bytes(), "merged bytes == parts concatenated in order")

    # Second run: parts present + merged complete -> nothing re-downloaded, no re-merge.
    _download_calls.clear()
    mtime = merged.stat().st_mtime_ns
    dl.download("vulcano_long_traverse_2025", ENTRY)
    check(len(_download_calls) == 3, "re-run still probes each part (cheap skip)")
    check(merged.stat().st_mtime_ns == mtime, "merge skipped when already complete")

    # Parts cleaned up to save space, merged kept -> short-circuit, no downloads.
    for u in PART_URLS:
        (dl.DOWNLOAD_DIR / dl.filename_from_url(u)).unlink()
    _download_calls.clear()
    dl.download("vulcano_long_traverse_2025", ENTRY)
    check(len(_download_calls) == 0, "no re-download when parts gone but merge present")
    check(merged.is_file(), "merged archive still intact after short-circuit")

    # A 'parts' entry without archive_name is a config error -> SystemExit.
    try:
        dl.download("broken", {"parts": PART_URLS})
        check(False, "missing archive_name should exit")
    except SystemExit:
        check(True, "missing archive_name raises SystemExit")

    if _failures:
        print(f"\n{len(_failures)} check(s) FAILED")
        return 1
    print("\nAll checks PASSED")
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    finally:
        shutil.rmtree(_TMP, ignore_errors=True)
    sys.exit(rc)
