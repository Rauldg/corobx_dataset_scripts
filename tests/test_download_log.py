#!/usr/bin/env python3
"""Host integration test for src/download_log.py.

Downloads the small 'test' log (a ~4 KB Readme.md published on Zenodo) into
ISPARO_DATA_DIR/downloads and checks it arrived. ISPARO_DATA_DIR comes from the
environment (the VSCode launch config sets it and selects the isparo_26 venv); if
unset it falls back to the repo, per download_log.py.

Run via the VSCode launch config, or directly:
    python3 tests/test_download_log.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

import download_log


def main():
    catalog = download_log.load_catalog()
    if "test" not in catalog:
        print("FAIL: no 'test' entry in logs.yaml")
        return 1
    entry = catalog["test"]

    dest = download_log.DOWNLOAD_DIR / download_log.filename_from_url(entry["url"])
    print(f"DOWNLOAD_DIR = {download_log.DOWNLOAD_DIR}")

    # force a fresh download so the test actually exercises the download
    if dest.exists():
        dest.unlink()

    download_log.download("test", entry)

    if dest.exists() and dest.stat().st_size > 0:
        print(f"PASS: downloaded {dest} ({dest.stat().st_size} bytes)")
        return 0
    print(f"FAIL: expected download not found or empty: {dest}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
