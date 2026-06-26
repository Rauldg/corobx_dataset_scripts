# Scripts to download, export to msgpack and import into python the logs collected by Coyote 3

The dataset contains the logs of the experiments described in the publication Field Testing of Rimless Wheeled Micro Rovers in Space Analogue Environments by Raúl Domı́nguez, Ravisankar Selvaraju, Felix Glinka, Christoph Hertzberg, Mehmed Yüksel and Frank Kirchner. Submitted to the Isparo 2026 conference.
The rover logs from the Long Traverse and from the SLAM experiment have been produced with the Rock robotics logger. Scripts to export the data to msgpack, a format that can be loaded into python as dataframes, are provided. From that point, it should be possible to convert to any desired format.


## Steps 

0. Run `download_log.py <log_key>` to download the log of an experiment. Without the `log_key` argument, the list of available logs are shown and nothing is downloaded.

0. Run the `convert_to_msgpack.py <log_key>` to convert from a rock log to msgpack files. The msgpack format by default converted to a nested format. To work with dataframes a relational format is more convinient. Thus, by default the conversion generates a `<stream_name>.msgpack` and a `<stream_name>_relational.msgpack`.

0. Run the `load_as_dataframe.py <log_key> <stream_key>` to load one relation msgpack file and see the summary of that stream. If no `<stream_key>` is passed the available stream_keys are displayed.

## Import standard formats into python

### Depthmaps

The script `import_depthmap.py` contains and example of how to import a .tiff file, the standard format used for the depthmaps. 

### Pointclouds

The pointclouds can be imported with any software that can import `.ply` files for instance cloud compare or meshlab.

