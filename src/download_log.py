#!/usr/bin/env python3
"""Download a log dataset listed in logs.yaml.

Usage:
    download_log.py             # list the available log_ids and exit
    download_log.py <log_id>    # download that log's archive into downloads/

The catalog (logs.yaml) maps each log_id to a ``description`` and a direct
``url`` (a Zenodo /content link). Archives are streamed into the package's
``downloads/`` folder; an already-complete download is skipped.
"""

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml

HERE = Path(__file__).resolve().parent
LOGS_YAML = HERE / "logs.yaml"
# Downloads/conversions live under ISPARO_DATA_DIR (default /data inside the image)
# so a host folder can be bind-mounted in; falls back to the repo for host runs.
DATA_DIR = Path(os.environ.get("ISPARO_DATA_DIR", HERE.parent))
DOWNLOAD_DIR = DATA_DIR / "downloads"

CHUNK = 1 << 16  # 64 KiB


def load_catalog():
    with open(LOGS_YAML) as f:
        return yaml.safe_load(f) or {}


def filename_from_url(url):
    """Derive the archive filename from a Zenodo download URL.

    Handles the ``.../files/<name>/content`` form as well as a plain
    ``.../<name>`` (optionally with a query string).
    """
    parts = [p for p in urlparse(url).path.split("/") if p]
    if parts and parts[-1] == "content" and len(parts) >= 2:
        return parts[-2]
    return parts[-1] if parts else "download.bin"


def list_logs(catalog):
    if not catalog:
        print(f"No logs listed in {LOGS_YAML}")
        return
    print("Available logs (pass a log_id to download):\n")
    for log_id, entry in catalog.items():
        desc = " ".join((entry.get("description") or "").split())
        if len(desc) > 100:
            desc = desc[:97] + "..."
        print(f"  {log_id}")
        if desc:
            print(f"      {desc}")
    print()


def download(log_id, entry):
    url = entry.get("url")
    if not url:
        sys.exit(f"Log '{log_id}' has no 'url' in {LOGS_YAML}")

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = DOWNLOAD_DIR / filename_from_url(url)
    tmp = dest.with_suffix(dest.suffix + ".part")

    print(f"Downloading '{log_id}'\n  from {url}\n  to   {dest}", flush=True)

    with requests.get(url, stream=True, allow_redirects=True) as r:
        if r.status_code == 404:
            sys.exit(
                "  -> 404 Not Found. If this is a Zenodo record, it is most "
                "likely still an unpublished draft (the public URL only works "
                "once the record is published)."
            )
        r.raise_for_status()

        total = int(r.headers.get("Content-Length", 0))
        if dest.exists() and total and dest.stat().st_size == total:
            print(f"  -> already downloaded ({total} bytes), skipping.")
            return dest

        done = 0
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=CHUNK):
                if not chunk:
                    continue
                f.write(chunk)
                done += len(chunk)
                _progress(done, total)
    print()  # finish the progress line

    tmp.replace(dest)
    print(f"  -> done: {dest} ({done} bytes)")
    return dest


def _progress(done, total):
    mb = done / (1 << 20)
    if total:
        pct = 100 * done / total
        sys.stderr.write(f"\r  {pct:5.1f}%  {mb:8.1f} MiB")
    else:
        sys.stderr.write(f"\r  {mb:8.1f} MiB")
    sys.stderr.flush()


def main(argv):
    catalog = load_catalog()

    if len(argv) < 2:
        list_logs(catalog)
        return 0

    log_id = argv[1]
    entry = catalog.get(log_id)
    if entry is None:
        print(f"Unknown log_id: {log_id}\n")
        list_logs(catalog)
        return 1

    download(log_id, entry)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
