#!/usr/bin/env python3
"""Load a converted stream as a pandas DataFrame and print a summary.

Usage:
    load_as_dataframe.py                    # list the available log_ids and exit
    load_as_dataframe.py <log_id>           # list the streams already converted for it
    load_as_dataframe.py <log_id> <stream>  # load that stream and print its statistics

This is the pure-Python load step: it reads the ``<stream>_relational.msgpack``
written by ``convert_to_msgpack.py`` with plain ``msgpack`` + ``pandas`` and never
touches Rock. The relational file stores one row per logged sample in a columnar
layout ``{port_name: {column: [values...]}}``; besides the data fields every
stream carries a ``timestamp`` column (microseconds since the Unix epoch) and a
``type`` column, which this script uses to report the sample rate.

As a convenience the first argument may also be a direct path to a
``*_relational.msgpack`` file, in which case it is loaded as-is.
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import msgpack
import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
LOGS_YAML = HERE / "logs.yaml"
# Downloads/conversions live under ISPARO_DATA_DIR (default /data inside the image)
# so a host folder can be bind-mounted in; falls back to the repo for host runs.
DATA_DIR = Path(os.environ.get("ISPARO_DATA_DIR", HERE.parent))
DOWNLOAD_DIR = DATA_DIR / "downloads"

RELATIONAL_SUFFIX = "_relational.msgpack"


def load_catalog():
    with open(LOGS_YAML) as f:
        return yaml.safe_load(f) or {}


def list_logs(catalog):
    if not catalog:
        print(f"No logs listed in {LOGS_YAML}")
        return
    print("Available logs (pass a log_id to list its converted streams):\n")
    for log_id, entry in catalog.items():
        desc = " ".join((entry.get("description") or "").split())
        if len(desc) > 100:
            desc = desc[:97] + "..."
        print(f"  {log_id}")
        if desc:
            print(f"      {desc}")
    print()


def msgpacks_dir(log_id):
    return DOWNLOAD_DIR / log_id / "msgpacks"


def list_converted_streams(log_id):
    """Print the streams already converted to relational msgpack for ``log_id``."""
    out_dir = msgpacks_dir(log_id)
    files = sorted(out_dir.glob(f"*{RELATIONAL_SUFFIX}")) if out_dir.is_dir() else []
    if not files:
        print(
            f"No converted streams found under {out_dir}\n"
            f"Run:  python3 src/convert_to_msgpack.py {log_id} <stream>   first."
        )
        return
    print(f"Converted streams for '{log_id}' (pass one to load it):\n")
    for f in files:
        print(f"  {f.name[:-len(RELATIONAL_SUFFIX)]}")
    print()


def resolve_relational(log_id, stream):
    """Return the path to the relational msgpack for ``stream`` of ``log_id``."""
    safe = stream.replace("/", "_")
    return msgpacks_dir(log_id) / f"{safe}{RELATIONAL_SUFFIX}"


def load_relational(path):
    """Load a relational msgpack into ``{port_name: DataFrame}``."""
    with open(path, "rb") as f:
        log = msgpack.unpack(f, raw=False)
    return {port: pd.DataFrame(columns) for port, columns in log.items()}


def _fmt_time(microseconds):
    """Render a microsecond Unix timestamp as an ISO-8601 UTC string."""
    dt = datetime.fromtimestamp(microseconds / 1e6, tz=timezone.utc)
    return dt.isoformat(timespec="milliseconds")


def summarize(port_name, df):
    """Print basic statistics for one stream's DataFrame."""
    rule = "=" * 78
    print(f"\n{rule}\n{port_name}\n{rule}")
    print(f"samples (rows): {len(df)}")
    print(f"columns:        {len(df.columns)}")

    if df.empty:
        print("(stream is empty)")
        return

    # Data type recorded by pocolog (constant per stream), shown once.
    if "type" in df.columns:
        types = df["type"].unique()
        print(f"logged type:    {', '.join(map(str, types))}")

    # Timing: timestamps are microseconds since the Unix epoch.
    if "timestamp" in df.columns:
        ts = df["timestamp"].astype("int64")
        t0, t1 = ts.iloc[0], ts.iloc[-1]
        span_s = (t1 - t0) / 1e6
        print("\nTiming")
        print(f"  first sample: {_fmt_time(t0)}  ({t0} us)")
        print(f"  last  sample: {_fmt_time(t1)}  ({t1} us)")
        print(f"  duration:     {span_s:.3f} s")
        if span_s > 0 and len(df) > 1:
            print(f"  mean rate:    {(len(df) - 1) / span_s:.3f} Hz")
        dt_ms = ts.diff().dropna() / 1e3  # inter-sample gaps in milliseconds
        if not dt_ms.empty:
            print(
                f"  sample dt ms: min {dt_ms.min():.3f} / "
                f"median {dt_ms.median():.3f} / max {dt_ms.max():.3f}"
            )

    # Per-column dtypes for the value columns (everything but the injected meta).
    value_cols = [c for c in df.columns if c not in ("timestamp", "type")]
    if value_cols:
        print("\nColumns")
        for col in value_cols:
            dtype = df[col].dtype
            note = ""
            if dtype == object and df[col].map(lambda v: isinstance(v, list)).all():
                lengths = df[col].map(len)
                note = (
                    f"  (list, len {lengths.min()})"
                    if lengths.min() == lengths.max()
                    else f"  (list, len {lengths.min()}-{lengths.max()})"
                )
            print(f"  {col}: {dtype}{note}")

    # describe() for the numeric value columns (skip timestamp/type and lists).
    numeric = df[value_cols].select_dtypes(include="number") if value_cols else df.iloc[:0]
    if not numeric.empty and numeric.shape[1] > 0:
        print("\nStatistics (numeric columns)")
        with pd.option_context("display.max_columns", None, "display.width", 120):
            print(numeric.describe().to_string())

    print("\nHead")
    with pd.option_context("display.max_columns", None, "display.width", 120):
        print(df.head().to_string())


def load_and_summarize(path):
    print(f"Loading {path}")
    frames = load_relational(path)
    if not frames:
        print("(file contains no streams)")
        return 0
    for port_name, df in frames.items():
        summarize(port_name, df)
    return 0


def main(argv):
    # Convenience: a direct path to a relational msgpack.
    if len(argv) >= 2 and argv[1].endswith(".msgpack") and Path(argv[1]).is_file():
        return load_and_summarize(Path(argv[1]))

    catalog = load_catalog()

    if len(argv) < 2:
        list_logs(catalog)
        return 0

    log_id = argv[1]
    if catalog.get(log_id) is None:
        print(f"Unknown log_id: {log_id}\n")
        list_logs(catalog)
        return 1

    if len(argv) < 3:
        list_converted_streams(log_id)
        return 0

    stream = argv[2]
    path = resolve_relational(log_id, stream)
    if not path.is_file():
        print(f"Relational msgpack not found: {path}\n")
        list_converted_streams(log_id)
        print(f"Run:  python3 src/convert_to_msgpack.py {log_id} {stream}   to create it.")
        return 1

    return load_and_summarize(path)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
