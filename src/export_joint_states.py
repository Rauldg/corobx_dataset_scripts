import msgpack
import os
import numpy as np
import inquirer
import json

def replace_nan_with_null(d):
    """Recursively replace NaN values with None in a dictionary."""
    for k, v in d.items():
        if isinstance(v, dict):
            replace_nan_with_null(v)
        elif isinstance(v, float) and np.isnan(v):
            d[k] = None

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

if log_name == "1112":
    MSGPACK_FILE = "/home/dockeruser/mount_datasets/20211117-1112/log_0_usefull_part_joint_states.0.msgpack"
    BASE_OUTPUT_FOLDER = "/home/dockeruser/mount_datasets/20211117-1112/joint_states/"
    stream_name = "hbridge_reader.status_samples"
elif log_name == "1140":
    MSGPACK_FILE = "/home/dockeruser/mount_datasets/20211117-1140/20211117-1140_usefull_interval_joint_states.0.msgpack"
    BASE_OUTPUT_FOLDER = "/home/dockeruser/mount_datasets/20211117-1140/joint_states/"
    stream_name = "hbridge_reader.status_samples"
elif log_name == "1205":
    MSGPACK_FILE = "/home/dockeruser/mount_datasets/20211117-1205/asguard_base_Logger_joint_states.0.msgpack"
    BASE_OUTPUT_FOLDER = "/home/dockeruser/mount_datasets/20211117-1205/joint_states/"
    stream_name = "hbridge_reader.status_samples"

log = msgpack.unpack(open(MSGPACK_FILE, "rb"))
print(log.keys())
joints_states = log[stream_name]

output_folder = BASE_OUTPUT_FOLDER + "joints_state_" + str(joints_states[0]['time']['microseconds'])

os.makedirs(output_folder, exist_ok=True)

for i, joints_state in enumerate(joints_states):
    filename = output_folder + "/joints_state_" + str(joints_state['time']['microseconds'])+".json"
    # 1. Make a dictionary with the values of ['names'] as keys
    # 2. Put inside each key the value of ['elements'] at [name_index]
    joint_state_dict = dict(zip(joints_state['names'], joints_state['elements']))
    replace_nan_with_null(joint_state_dict)
    # 3. Save the dictionary as a json file
    with open(filename, 'w') as f:
        json.dump(joint_state_dict, f)
    print("Saved joint state to: " + filename)
