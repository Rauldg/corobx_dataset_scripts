import msgpack
import os
import numpy as np
import tifffile as tiff
import inquirer

options = [
    "1112",
    "1140",
    "1205_1_laser_scans",
    "1205_2_laser_scans",
    "1205_3_laser_scans",
]

# Create an interactive menu
questions = [
    inquirer.List(
        'log_name',
        message="Select the value for log_name",
        choices=options,
    ),
]

# Get the selected value
answers = inquirer.prompt(questions)
log_name = answers['log_name']

print(f"Selected log_name: {log_name}")

TO_EXPORT = "velodyne.laser_scans"
#TO_EXPORT = "outlier_filter.filtered_depth_map" # Not available, was not logged
DEBUG_ONLY_DEPTH = False
DEBUG_ONLY_ONE = False

if log_name == "1112":
    MSGPACK_FILE = "/home/dockeruser/mount_datasets/20211117-1112/log_0_usefull_part_depthmaps.0.msgpack"
    OUTPUT_FOLDER = "/home/dockeruser/mount_datasets/20211117-1112/depth/"
    FILENAME_PREFIX = "depth_"
elif log_name == "1140":
    MSGPACK_FILE = "/home/dockeruser/mount_datasets/20211117-1140/20211117-1140_usefull_interval_depthmaps.0.msgpack"
    OUTPUT_FOLDER = "/home/dockeruser/mount_datasets/20211117-1140/depth/"
    FILENAME_PREFIX = "depth_"
elif log_name == "1205_1_laser_scans": 
    MSGPACK_FILE = "/home/dockeruser/mount_datasets/20211117-1205/laser_scanner_Logger_until_2000_laser_scans.0.msgpack"
    OUTPUT_FOLDER = "/home/dockeruser/mount_datasets/20211117-1205/depth/"
    FILENAME_PREFIX = "depth_"
elif log_name == "1205_2_laser_scans": 
    MSGPACK_FILE = "/home/dockeruser/mount_datasets/20211117-1205/laser_scanner_Logger_from_2000_until_4000_laser_scans.0.msgpack"
    OUTPUT_FOLDER = "/home/dockeruser/mount_datasets/20211117-1205/depth/"
    FILENAME_PREFIX = "depth_"
elif log_name == "1205_3_laser_scans": 
    MSGPACK_FILE = "/home/dockeruser/mount_datasets/20211117-1205/laser_scanner_Logger_from_4000_laser_scans.0.msgpack"
    OUTPUT_FOLDER = "/home/dockeruser/mount_datasets/20211117-1205/depth/"
    FILENAME_PREFIX = "depth_"


#elif TO_EXPORT == "outlier_filter.filtered_depth_map":
#    # For the filtered depth maps
#    MSGPACK_FILE = "/home/dockeruser/mount_datasets/20211117-1112/depth_map_converter_slam.0.msgpack"
#    OUTPUT_FOLDER = "/home/dockeruser/mount_datasets/20211117-1112/filtered_depth/"
#    FILENAME_PREFIX = "filtered_depth_"




def normalize(array):
    """Normalize the array to the range [0, 1]."""
    array_min, array_max = array.min(), array.max()
    return (array - array_min) / (array_max - array_min)

def replace_inf_with_max(array):
    """Replace inf values with the maximum non-inf value in the array."""
    finite_max = np.max(array[np.isfinite(array)])
    array[np.isinf(array)] = finite_max
    return array

def save_depth_and_metadata_to_tiff(
    depth_map, remissions, timestamp_map, filename, metadata
):
    """
    Save depth map, remissions, timestamps, and metadata to a TIFF file.

    Parameters:
        depth_map (numpy.ndarray): 2D array of depth values (float64).
        remissions (numpy.ndarray): 2D array of remission values (float64).
        timestamp_map (numpy.ndarray): 2D array of timestamps (float64).
        filename (str): Path to the output TIFF file.
        metadata (dict): Dictionary of metadata fields to include in the header.
    """
    if depth_map.shape != timestamp_map.shape:
        raise ValueError("Depth map and timestamp map must have the same shape.")
    
    if depth_map.shape != remissions.shape:
        raise ValueError("Depth map and remissions map must have the same shape.")
    
    finite_max = np.max(depth_map[np.isfinite(depth_map)])
    print("Min max (not inf) max (possibly inf) depth: ", np.min(depth_map), finite_max, np.max(depth_map))

    # Stack the depth and timestamp maps into a multi-channel array
    multi_channel_data = np.stack((depth_map, remissions, timestamp_map), axis=-1).astype(np.float64)

    if DEBUG_ONLY_DEPTH:
        debug_non_inf_depth_map = replace_inf_with_max(depth_map.astype(np.float64))
        print("Min max depth: ", np.min(debug_non_inf_depth_map), np.max(debug_non_inf_depth_map))
        print("Normalized Min max depth: ", np.min(normalize(debug_non_inf_depth_map)), np.max(normalize(debug_non_inf_depth_map)))
        multi_channel_data = normalize(debug_non_inf_depth_map)


    # Save to a TIFF file with metadata
    with tiff.TiffWriter(filename) as tiff_writer:
        tiff_writer.write(
            multi_channel_data,
            photometric="minisblack",
            planarconfig="contig",   #Ensure vertical bands are stored in the same plane
            metadata=metadata,
            shape=multi_channel_data.shape,
            dtype=np.float64,
        )

log = msgpack.unpack(open(MSGPACK_FILE, "rb"))

# velodyne.laser_scans.meta['timestamps'] - Timestamp of each depthmap, to be used for the filename

# velodyne.laser_scans[i]['time']['microseconds'] -  Timestamp of the depthmap can be used for the title
# velodyne.laser_scans[i]['timestamps'][j]['microseconds'] - Timestamp of the j pixel
# velodyne.laser_scans[i]['distances'] - vector of distances
# velodyne.laser_scans[i]['remissions'] - vector of remissions
# There are other metadata fields that should be added to the tiff header:
# velodyne.laser_scans[i]
# vertical_projection
# horizontal_projection
# vertical_interval
# horizontal_interval
# vertical_size
# horizontal_size

#print(log.keys())


depth_maps = log[TO_EXPORT]


output_folder = OUTPUT_FOLDER + FILENAME_PREFIX + str(depth_maps[0]['time']['microseconds'])
os.makedirs(output_folder, exist_ok=True)

if DEBUG_ONLY_ONE:
    depth_maps = [depth_maps[0]]

for i, depth in enumerate(depth_maps):
    filename = output_folder + "/depth_" + str(depth['time']['microseconds'])+".tiff"
    distances = np.array(depth['distances'],dtype=np.float64).reshape((depth['vertical_size'], depth['horizontal_size']))
    remissions = np.array(depth['remissions'],dtype=np.float64).reshape((depth['vertical_size'], depth['horizontal_size']))
    timestamps_list = [timestamp['microseconds'] for timestamp in depth['timestamps']]
    timestamps = np.array(timestamps_list, dtype=np.float64).reshape((1, -1)).repeat(depth['vertical_size'], axis=0)
    metadata = {
        "vertical_projection": depth['vertical_projection'],
        "horizontal_projection": depth['horizontal_projection'],
        "vertical_interval": depth['vertical_interval'],
        "horizontal_interval": depth['horizontal_interval'],
        "vertical_size": depth['vertical_size'],
        "horizontal_size": depth['horizontal_size'],    
    }
    save_depth_and_metadata_to_tiff(distances, remissions, timestamps, filename, metadata)
    print("Saved depthmap to: " + filename)

