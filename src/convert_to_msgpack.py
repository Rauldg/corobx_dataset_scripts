#!/usr/bin/env python3
"""Convert a downloaded Rock pocolog log to msgpack.

Usage:
    convert_to_msgpack.py                    # list the available log_ids and exit
    convert_to_msgpack.py <log_id>           # extract (if needed) and list its streams
    convert_to_msgpack.py <log_id> <stream>  # convert that stream to msgpack

With a stream name, the stream is written as a nested ``<stream>.msgpack`` (via
``pocolog2msgpack --only``) and a relational ``<stream>_relational.msgpack`` (via the
``pocolog2msgpack`` Python module's ``object2relational``). The archive named in
logs.yaml must already be present in downloads/ (run ``download_log.py <log_id>``
first). Conversion relies on the ``pocolog2msgpack`` binary + module, which are
provided by the isparo_scripts Docker image.
"""

import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import msgpack
import yaml

HERE = Path(__file__).resolve().parent
LOGS_YAML = HERE / "logs.yaml"
# Downloads/conversions live under ISPARO_DATA_DIR (default /data inside the image)
# so a host folder can be bind-mounted in; falls back to the repo for host runs.
DATA_DIR = Path(os.environ.get("ISPARO_DATA_DIR", HERE.parent))
DOWNLOAD_DIR = DATA_DIR / "downloads"

POCOLOG2MSGPACK = "pocolog2msgpack"


def load_catalog():
    with open(LOGS_YAML) as f:
        return yaml.safe_load(f) or {}


def list_logs(catalog):
    if not catalog:
        print(f"No logs listed in {LOGS_YAML}")
        return
    print("Available logs (pass a log_id to list its streams):\n")
    for log_id, entry in catalog.items():
        desc = " ".join((entry.get("description") or "").split())
        if len(desc) > 100:
            desc = desc[:97] + "..."
        print(f"  {log_id}")
        if desc:
            print(f"      {desc}")
    print()


def ensure_extracted(log_id, entry):
    """Extract the log_id's archive into downloads/<log_id>/ (idempotent); return that dir."""
    archive_name = entry.get("archive_name")
    if not archive_name:
        sys.exit(f"Log '{log_id}' has no 'archive_name' in {LOGS_YAML}")

    archive = DOWNLOAD_DIR / archive_name
    if not archive.exists():
        sys.exit(
            f"Archive not found: {archive}\n"
            f"Run:  python3 src/download_log.py {log_id}"
        )

    dest = DOWNLOAD_DIR / log_id
    marker = dest / ".extracted"
    if marker.exists():
        return dest

    dest.mkdir(parents=True, exist_ok=True)
    print(f"Extracting {archive.name} -> {dest}\n  (this can take a while for large archives)...")
    with tarfile.open(archive, "r:gz") as tar:
        try:
            tar.extractall(dest, filter="data")  # py>=3.12 safe-extraction filter
        except TypeError:
            tar.extractall(dest)
    marker.touch()
    return dest


def list_streams(log_file):
    """Return the stream/port names in a pocolog .log file.

    Cheap probe: convert only the first sample of each stream to a throwaway
    msgpack, then read its top-level keys (the stream names; ``*.meta`` entries
    hold metadata and are filtered out).
    """
    with tempfile.NamedTemporaryFile(suffix=".msgpack", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        subprocess.run(
            [POCOLOG2MSGPACK, "-l", str(log_file), "--end", "1", "-o", str(tmp_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        with open(tmp_path, "rb") as f:
            data = msgpack.unpack(f, raw=False)
        return sorted(k for k in data.keys() if not k.endswith(".meta"))
    finally:
        tmp_path.unlink(missing_ok=True)


def list_log_streams(log_id, entry):
    if shutil.which(POCOLOG2MSGPACK) is None:
        sys.exit(
            f"'{POCOLOG2MSGPACK}' not found on PATH. It is provided by the devel "
            f"image; source the tool's env.sh first."
        )

    dest = ensure_extracted(log_id, entry)
    log_files = sorted(dest.rglob("*.log"))
    if not log_files:
        sys.exit(f"No .log files found under {dest}")

    print(f"\nStreams in '{log_id}' ({len(log_files)} log file(s)):")
    for log_file in log_files:
        print(f"\n  {log_file.relative_to(dest)}")
        try:
            streams = list_streams(log_file)
        except subprocess.CalledProcessError as e:
            print(f"      [pocolog2msgpack failed: {(e.stderr or '').strip() or e}]")
            continue
        if not streams:
            print("      (no streams)")
        for stream in streams:
            print(f"      - {stream}")


def find_log_for_stream(dest, stream):
    """Return the extracted .log file that contains ``stream``, or None.

    Each .log holds many streams and a stream's file is not derivable from the
    file name, so probe with ``list_streams``. Smallest files first keeps it cheap:
    small logs are checked before the large ones.
    """
    for log_file in sorted(dest.rglob("*.log"), key=lambda p: p.stat().st_size):
        if stream in list_streams(log_file):
            return log_file
    return None


def convert_stream(log_id, entry, stream):
    if shutil.which(POCOLOG2MSGPACK) is None:
        sys.exit(
            f"'{POCOLOG2MSGPACK}' not found on PATH. It is provided by the "
            f"isparo_scripts image."
        )

    dest = ensure_extracted(log_id, entry)
    log_file = find_log_for_stream(dest, stream)
    if log_file is None:
        sys.exit(
            f"Stream '{stream}' not found in any log of '{log_id}'.\n"
            f"Run:  python3 src/convert_to_msgpack.py {log_id}   to list valid streams."
        )

    out_dir = dest / "msgpacks"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = stream.replace("/", "_")
    nested = out_dir / f"{safe}.msgpack"
    relational = out_dir / f"{safe}_relational.msgpack"

    print(f"Converting '{stream}'\n  from {log_file.relative_to(dest)}\n  ->   {nested}")
    try:
        subprocess.run(
            [POCOLOG2MSGPACK, "-l", str(log_file), "--only", stream, "-o", str(nested)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        sys.exit(f"pocolog2msgpack failed: {(e.stderr or '').strip() or e}")

    # relational form: pure-Python, and only needed here, so import lazily
    from pocolog2msgpack import object2relational

    object2relational(str(nested), str(relational))
    print(f"  ->   {relational}")
    return 0


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

    if len(argv) >= 3:
        return convert_stream(log_id, entry, argv[2])

    list_log_streams(log_id, entry)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
