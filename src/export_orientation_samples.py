import msgpack
import os
import numpy as np
import inquirer
import json

def replace_nan_with_null(d):
    """Recursively replace NaN values with None in a dictionary or list."""
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, (dict, list)):
                replace_nan_with_null(v)
            elif isinstance(v, float) and np.isnan(v):
                d[k] = None
    elif isinstance(d, list):
        for i in range(len(d)):
            if isinstance(d[i], (dict, list)):
                replace_nan_with_null(d[i])
            elif isinstance(d[i], float) and np.isnan(d[i]):
                d[i] = None

# Define the options for LOG_NAME
options = [
    "1112",
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
stream_name = "xsens.orientation_samples"

if log_name == "1112":
    MSGPACK_FILE = "/home/dockeruser/mount_datasets/20211117-1112/log_0_usefull_part_orientation_samples.0.msgpack"
    BASE_OUTPUT_FOLDER = "/home/dockeruser/mount_datasets/20211117-1112/orientation_samples/"
elif log_name == "1140":
    MSGPACK_FILE = "/home/dockeruser/mount_datasets/20211117-1140/20211117-1140_usefull_interval_orientation_samples.0.msgpack"
    BASE_OUTPUT_FOLDER = "/home/dockeruser/mount_datasets/20211117-1140/orientation_samples/"
elif log_name == "1205":
    MSGPACK_FILE = "/home/dockeruser/mount_datasets/20211117-1205/xsens_Logger_orientation_samples.0.msgpack"
    BASE_OUTPUT_FOLDER = "/home/dockeruser/mount_datasets/20211117-1205/orientation_samples/"

log = msgpack.unpack(open(MSGPACK_FILE, "rb"))
print(log.keys())
orientation_samples = log[stream_name]

output_folder = BASE_OUTPUT_FOLDER + "orientation_sample_" + str(orientation_samples[0]['time']['microseconds'])

os.makedirs(output_folder, exist_ok=True)

for i, orientation_sample in enumerate(orientation_samples):
    filename = output_folder + "/orientation_sample_" + str(orientation_sample['time']['microseconds'])+".json"
    replace_nan_with_null(orientation_sample)
    # 3. Save the dictionary as a json file
    with open(filename, 'w') as f:
        json.dump(orientation_sample, f)
    print("Saved orientation sample to: " + filename)
