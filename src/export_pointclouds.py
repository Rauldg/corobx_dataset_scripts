import pocolog2msgpack
import pexpect
import msgpack
import os
import open3d as o3d
import trimesh
import numpy as np
import inquirer

# Define the options for LOG_NAME
options = [
    "1112_part1",
    "1112_part2",
    "1140",
    "1205"
]

# Create an interactive menu
questions = [
    inquirer.List(
        'log_name',
        message="Select the value for LOG_NAME",
        choices=options,
    ),
]

# Get the selected value
answers = inquirer.prompt(questions)
log_name = answers['log_name']

print(f"Selected log_name: {log_name}")

if log_name == "1112_part1":
    MSGPACK_FILE = "/home/dockeruser/mount_datasets/20211117-1112/depth_map_converter_slam_until_2000.0.msgpack"
    BASE_OUTPUT_FOLDER = "/home/dockeruser/mount_datasets/20211117-1112/filtered_cloud/"
    stream_name = "/depth_map_converter_slam.cloud"
elif log_name == "1112_part2":
    MSGPACK_FILE = "/home/dockeruser/mount_datasets/20211117-1112/depth_map_converter_slam_start_at_2000.0.msgpack"
    BASE_OUTPUT_FOLDER = "/home/dockeruser/mount_datasets/20211117-1112/filtered_cloud/"
    stream_name = "/depth_map_converter_slam.cloud"
elif log_name == "1140":
    MSGPACK_FILE = "/home/dockeruser/mount_datasets/20211117-1140/depth_map_converter_slam.0.msgpack"
    BASE_OUTPUT_FOLDER = "/home/dockeruser/mount_datasets/20211117-1140/filtered_cloud/"
    stream_name = "/depth_map_converter_slam.cloud"
elif log_name == "1205":
    MSGPACK_FILE = "/home/dockeruser/mount_datasets/20211117-1205/laser_scanner_Logger_pointcloud.0.msgpack"
    BASE_OUTPUT_FOLDER = "/home/dockeruser/mount_datasets/20211117-1205/filtered_cloud/"
    stream_name = "depth_map_converter.pointcloud"

 

log = msgpack.unpack(open(MSGPACK_FILE, "rb"))
print(log.keys())
pcds = log[stream_name]

#print(pcds[0])

output_folder = BASE_OUTPUT_FOLDER + "cloud_" + str(pcds[0]['time']['microseconds'])

os.makedirs(output_folder, exist_ok=True)

for i, pcd in enumerate(pcds):
    filename = output_folder + "/cloud_" + str(pcd['time']['microseconds'])+".ply"
    points = np.array([point['data'] for point in pcd['points']], dtype=np.float32)  # Convert to numpy array of size n,3
    if len(points) > 0:
        point_cloud = trimesh.PointCloud(points)
        point_cloud.export(filename, file_type="ply")   
        print("Saved point cloud to: " + filename)
    else:
        print("Skipping empty point cloud at: " + filename)
    
