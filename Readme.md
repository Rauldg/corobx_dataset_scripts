# Scripts to export and import the logs collected by Asguard v4 for SLAM

The dataset contains the samples used to generate the map provided as ground truth in the publication <TODO: ADD Title>

*NOTE:* The dataset has three parts. Between each of the parts, the data capture had to be interrupted. After each interruption, the position of the rover is not exactly the same as before the interruption. For that reason, it has been quite challenging to generate a full reconstruction using the three parts one after the other. In fact, the last part of the log has not been fully filtered, since it was not possible to combine the first and second part, this last part was not pre-processed.

## Steps to export to standard formats

0. Run the `convert_<datatype>.py` to import convert from rock logs to msgpack files. 

0. Run the `export_<datatype>.py` to export from the msgpack files to the separate files containing each one a single sample of <datatype>

## Import standard formats into python

### Depthmaps

The script `import_depthmap.py` contains and example of how to import a .tiff file, the standard format used for the depthmaps. 

### Pointclouds

The pointclouds can be imported with any software that can import `.ply` files for instance cloud compare or meshlab.

