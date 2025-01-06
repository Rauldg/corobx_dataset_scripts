import inquirer
import pexpect

options = [
    "1112",
    "1140", 
    "1205",
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

ONLY = "--only hbridge_reader.status_samples"

if log_name == "1112":
    ROCK_LOG_FILE = "/home/dockeruser/mount_datasets/20211117-1112/log_0_useful_part.0.log"
    OUTPUT_FILE = "/home/dockeruser/mount_datasets/20211117-1112/log_0_usefull_part_joint_states.0.msgpack"
    ONLY = "--only hbridge_reader.status_samples"
    RANGE = ""
elif log_name == "1140":
    ROCK_LOG_FILE = "/home/dockeruser/mount_datasets/20211117-1140/20211117-1140_usefull_interval.0.log"
    OUTPUT_FILE = "/home/dockeruser/mount_datasets/20211117-1140/20211117-1140_usefull_interval_joint_states.0.msgpack"
    ONLY = "--only hbridge_reader.status_samples"
    RANGE = ""
elif log_name == "1205":
    ROCK_LOG_FILE = "/home/dockeruser/mount_datasets/20211117-1205/asguard_base_Logger.0.log"
    OUTPUT_FILE = "/home/dockeruser/mount_datasets/20211117-1205/asguard_base_Logger_joint_states.0.msgpack"
    ONLY = "--only hbridge_reader.status_samples"
    RANGE = "--end 2000"



cmd = "pocolog2msgpack -l %s %s %s -o %s" % (ROCK_LOG_FILE, ONLY, RANGE, OUTPUT_FILE)
print("Command: " + cmd)
proc = pexpect.spawn(cmd, timeout=300)
proc.expect(pexpect.EOF)