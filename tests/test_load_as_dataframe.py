#!/usr/bin/env python3
"""Host test for src/load_as_dataframe.py.

Uses a real stream from the dataset: a 100-sample slice of
``coyote3_odometry.odometry_samples`` (a /base/samples/RigidBodyState pose,
extracted with the step-2 convert), committed under tests/fixtures/. That gives
the loader a genuine multi-field relational layout to chew on — scalar ints,
floats and strings plus vector/covariance columns (position.data, cov_*.data,
orientation.im, ...) — instead of hand-made data. See tests/fixtures/README.md
for how the fixture was produced.

The test stays hermetic: it points ISPARO_DATA_DIR at a fresh temp dir and copies
the fixture into the msgpacks/ layout the loader expects, so it needs no network,
no full dataset and no Docker. It just needs the isparo_26 venv (msgpack+pandas).

Run via the VSCode launch config, or directly:
    python3 tests/test_load_as_dataframe.py
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

# Point the module's DATA_DIR at a throwaway dir *before* importing it (the
# module reads ISPARO_DATA_DIR at import time). This keeps the test hermetic and
# independent of whatever real ISPARO_DATA_DIR the launch config may set.
_TMP = tempfile.mkdtemp(prefix="isparo_load_test_")
os.environ["ISPARO_DATA_DIR"] = _TMP

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

import load_as_dataframe as lad  # noqa: E402

# 'test' is a real log_id in logs.yaml, so main() passes its catalog check.
LOG_ID = "test"
STREAM = "coyote3_odometry.odometry_samples"
FIXTURE = HERE / "fixtures" / f"{STREAM}_relational.msgpack"

# Known facts about the committed fixture (a real slice of the dataset).
N_ROWS = 100
EXPECT_COLUMNS = [
    "time.microseconds", "sourceFrame", "targetFrame", "position.data",
    "cov_position.data", "orientation.im", "orientation.re", "cov_orientation.data",
    "velocity.data", "cov_velocity.data", "angular_velocity.data",
    "cov_angular_velocity.data", "timestamp", "type",
]
EXPECT_TYPE = "/base/samples/RigidBodyState_m"
EXPECT_SOURCE_FRAME = "coyote3_base_link"
EXPECT_FIRST_TS = 1718793486897587  # first 'timestamp' (microseconds since epoch)

_failures = []


def check(cond, msg):
    print(("PASS: " if cond else "FAIL: ") + msg)
    if not cond:
        _failures.append(msg)


def install_fixture():
    """Copy the committed fixture into the loader's msgpacks/ layout; return its path."""
    dest = lad.resolve_relational(LOG_ID, STREAM)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE, dest)
    return dest


def main():
    print(f"ISPARO_DATA_DIR = {lad.DATA_DIR}")
    check(FIXTURE.is_file(), f"fixture present: {FIXTURE}")

    path = install_fixture()
    # resolve_relational maps <stream> to <stream>_relational.msgpack under msgpacks/
    check(
        path == lad.msgpacks_dir(LOG_ID) / f"{STREAM}_relational.msgpack",
        "resolve_relational builds the expected msgpacks/ path",
    )

    # load_relational returns {port: DataFrame} matching the real stream layout.
    frames = lad.load_relational(path)
    check(list(frames) == [STREAM], f"single port loaded: {list(frames)}")
    df = frames[STREAM]
    check(len(df) == N_ROWS, f"row count == {N_ROWS} (got {len(df)})")
    check(list(df.columns) == EXPECT_COLUMNS, "all real columns preserved in order")

    # Field-level checks across the mixed scalar/vector layout.
    check(str(df["orientation.re"].dtype) == "float64", "orientation.re is float64")
    check(
        df["position.data"].map(lambda v: isinstance(v, list) and len(v) == 3).all(),
        "position.data is a length-3 vector column",
    )
    check(
        df["cov_position.data"].map(lambda v: isinstance(v, list) and len(v) == 9).all(),
        "cov_position.data is a length-9 covariance column",
    )
    check((df["type"] == EXPECT_TYPE).all(), f"type column == {EXPECT_TYPE}")
    check((df["sourceFrame"] == EXPECT_SOURCE_FRAME).all(), "sourceFrame is the real frame name")
    check(int(df["timestamp"].iloc[0]) == EXPECT_FIRST_TS, "first timestamp matches the log")
    check(df["timestamp"].is_monotonic_increasing, "timestamps are monotonic")

    # summarize must run cleanly on this real, multi-field frame.
    try:
        lad.summarize(STREAM, df)
        check(True, "summarize() ran without error")
    except Exception as e:  # noqa: BLE001
        check(False, f"summarize() raised: {e!r}")

    # Full main() flow: known log_id + existing stream -> 0.
    check(lad.main(["load_as_dataframe.py", LOG_ID, STREAM]) == 0, "main() returns 0 for a valid stream")

    # Negative case: a stream with no msgpack -> non-zero, and no crash.
    check(
        lad.main(["load_as_dataframe.py", LOG_ID, "does_not_exist.stream"]) == 1,
        "main() returns 1 for a missing stream",
    )

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
