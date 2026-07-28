# Coyote 3 dataset scripts — download, convert to msgpack, load in Python

The dataset contains the logs of the experiments described in the publication
*Field Testing of Rimless Wheeled Micro Rovers in Space Analogue Environments* by
Raúl Domínguez, Ravisankar Selvaraju, Felix Glinka, Christoph Hertzberg, Mehmed
Yüksel and Frank Kirchner (submitted to the ISPARO 2026 conference).

The rover logs (Long Traverse and SLAM experiment) were recorded with the Rock
robotics logger. The scripts of this package download the logs, convert its streams to msgpack (a
format that can be loaded into Python as dataframes) and provide a simple load example for analysis. From
the msgpack it is straightforward to convert to any other format.

## Requirements

- **Python 3 + pip** — for the download and load steps (1 and 3).
- **Docker** — only for the conversion step (2), which uses the `pocolog2msgpack`
  / ROCK toolchain bundled in a Docker image. The ROCK installation is not needed to be done by the user. The needed ROCK packages are bundled in the Docker image.

## Setup

Install the Python dependencies for the host-side steps:

```bash
pip install -r requirements.txt
```

Build the Docker image used by the conversion step (or pull the published one,
once available):

```bash
docker build -t isparo_scripts .
```

Choose a folder of your filesystem for the storage of the data and point the environment variable `ISPARO_DATA_DIR` at it. Both the host
scripts and the conversion container read from and write into that folder, so all steps use the
same folder:

```bash
export ISPARO_DATA_DIR="$PWD/isparo_data"
mkdir -p "$ISPARO_DATA_DIR"
```

## Steps

1. **Download** a log — *no docker required*. Without a `<log_id>` the available logs
   are listed and nothing is downloaded. The archive is saved under
   `$ISPARO_DATA_DIR/downloads/`.
   ```bash
   python3 src/download_log.py vulcano_long_traverse_2024
   ```

2. **Convert** a log to msgpack — *docker required* (the only step that needs the
   `pocolog2msgpack` / Rock toolchain). Without a `<log_id>` the available logs are
   listed. With a `<log_id>` the archive is extracted and its **streams are
   listed**; pass a `<stream>` to convert that stream to a nested `<name>.msgpack`
   and a relational `<name>_relational.msgpack`.
   ```bash
   docker run --rm -u "$(id -u):$(id -g)" -v "$ISPARO_DATA_DIR:/data" \
       isparo_scripts python3 src/convert_to_msgpack.py vulcano_long_traverse_2024
   ```

3. **Load** a converted stream as a pandas DataFrame and print its summary — *no docker required*. It reads the relational msgpack with plain `msgpack` + `pandas`
   and never touches Rock.
   ```bash
   python3 src/load_as_dataframe.py vulcano_long_traverse_2024 <stream>
   ```

## Notes

- **Shared data folder**: the host steps use `ISPARO_DATA_DIR`; the conversion
  container is given that same folder via `-v "$ISPARO_DATA_DIR:/data"` (inside the
  container the path is always `/data`). That is why all three steps see the same
  files.
- **File ownership**: `-u "$(id -u):$(id -g)"` makes the files the container writes
  owned by you, so the host load step can read them.
- **Large logs**: some archives are tens of GB and expand further on extraction —
  make sure `ISPARO_DATA_DIR` has enough free space.
- **No Python on your machine?** The image bundles all three scripts, so you can
  also run the download and load steps through it, e.g. `docker run --rm -u
  "$(id -u):$(id -g)" -v "$ISPARO_DATA_DIR:/data" isparo_scripts python3
  src/download_log.py <log_id>`.
