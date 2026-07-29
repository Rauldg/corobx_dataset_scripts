# Test fixtures

Small, real relational-msgpack slices used by the host tests so they can run
without downloading a full dataset or running the Docker conversion.

## `coyote3_odometry.odometry_samples_relational.msgpack`

The first **100 samples** of the `coyote3_odometry.odometry_samples` stream
(a `/base/samples/RigidBodyState` pose) from the `vulcano_long_traverse_2024`
log. It keeps the stream's real, multi-field layout — scalar ints/floats/strings
plus vector and covariance columns — which is exactly what `load_as_dataframe.py`
has to handle.

Used by `tests/test_load_as_dataframe.py`.

### How it was regenerated

Convert the stream from the full dataset (step 2 in the package Readme), then
slice the first 100 samples of every column:

```bash
export ISPARO_DATA_DIR=/path/to/isparo_datadir
docker run --rm -u "$(id -u):$(id -g)" -v "$ISPARO_DATA_DIR:/data" \
    isparo_scripts python3 src/convert_to_msgpack.py \
    vulcano_long_traverse_2024 coyote3_odometry.odometry_samples

python3 - <<'PY'
import msgpack
src = "$ISPARO_DATA_DIR/downloads/vulcano_long_traverse_2024/msgpacks/coyote3_odometry.odometry_samples_relational.msgpack"
dst = "tests/fixtures/coyote3_odometry.odometry_samples_relational.msgpack"
with open(src, "rb") as f:
    log = msgpack.unpack(f, raw=False)
sliced = {port: {c: v[:100] for c, v in cols.items()} for port, cols in log.items()}
with open(dst, "wb") as f:
    msgpack.pack(sliced, f)
PY
```
