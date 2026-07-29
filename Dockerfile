# Distributable image for the ft_rwr_isparo_2026 dataset scripts.
#
# It bundles the scripts + their Python dependencies + the pocolog2msgpack
# toolchain, so a user needs nothing but Docker and a host folder to mount at
# /data (downloads and conversions are written there).
#
# Build (needs the pocolog2msgpack:24.04 image available locally):
#   docker build -t isparo_scripts .
#
# Run (data persists in ./isparo_data on the host; run as your own uid so the
# files it writes are owned by you, not root):
#   docker run --rm -u "$(id -u):$(id -g)" -v "$PWD/isparo_data:/data" \
#       isparo_scripts python3 src/download_log.py vulcano_log_traverse_2024

FROM rauldg/pocolog2msgpack:24.04

# the scripts and their Python dependencies
# (installed system-wide into /usr/local; Ubuntu 24.04 is PEP-668 "externally managed")
COPY . /opt/isparo_scripts
RUN python3 -m pip install --break-system-packages \
        -r /opt/isparo_scripts/requirements.txt

# Make the pocolog2msgpack binary, its shared libraries and its Python module
# available without sourcing /opt/rock/env.sh at runtime (that helper reads
# /root/.local and errors for non-root users). These mirror what env.sh exports.
ENV PATH=/opt/rock/install/bin:/opt/rock/install/pip/bin:$PATH \
    LD_LIBRARY_PATH=/opt/rock/install/lib \
    PYTHONPATH=/opt/rock/install/pip/lib/python3.12/site-packages \
    PKG_CONFIG_PATH=/opt/rock/install/lib/pkgconfig \
    ISPARO_DATA_DIR=/data

WORKDIR /opt/isparo_scripts

# reset the base image's ENTRYPOINT (/opt/rock/run.sh, which sources env.sh and
# runs pocolog2msgpack) so the given command runs directly with the env above
ENTRYPOINT []
# default: list the available logs (run with explicit args to download/convert)
CMD ["python3", "src/convert_to_msgpack.py"]
