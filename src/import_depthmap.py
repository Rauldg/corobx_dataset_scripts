import numpy as np
import tifffile as tiff
import json

def load_depth_and_metadata_from_tiff(filename):
    """
    Load depth map, remissions, and timestamp map from a TIFF file.

    Parameters:
        filename (str): Path to the input TIFF file.

    Returns:
        tuple: A tuple containing:
            - depth_map (numpy.ndarray): 2D array of depth values (float64).
            - remissions (numpy.ndarray): 2D array of remission values (float64).
            - timestamp_map (numpy.ndarray): 2D array of timestamps (float64).
            - metadata (dict): Dictionary of metadata fields from the header.
    """
    with tiff.TiffFile(filename) as tif:
        # Read the multi-channel data
        multi_channel_data = tif.asarray()
        
        # Extract metadata
        metadata = tif.pages[0].tags['ImageDescription'].value
        metadata = json.loads(metadata)

        # Extract individual channels
        depth_map = multi_channel_data[:, :, 0].astype(np.float64)
        remissions = multi_channel_data[:, :, 1].astype(np.float64)
        timestamp_map = multi_channel_data[:, :, 2].astype(np.float64)

    return depth_map, remissions, timestamp_map, metadata

# Example usage
filename = "/home/dockeruser/mount_datasets/20211117-1112/depth/depth_1637143958347198/depth_1637143958347198.tiff"
depth_map, remissions, timestamp_map, metadata = load_depth_and_metadata_from_tiff(filename)
print("Depth Map size and first 3 rows:", depth_map)
print("Remission size and first 3 rows:", remissions)
print("Timestamp Map and firsr 3 rows:", timestamp_map)
print("Metadata:", metadata)