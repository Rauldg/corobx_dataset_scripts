import inquirer
import pexpect

options = [
    "1112",
    "1140", 
    "1205_1_laser_scans",
    "1205_2_laser_scans",
    "1205_3_laser_scans"
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

TO_CONVERT = "raw_depth_maps"

if log_name == "1112":
    ROCK_LOG_FILE = "/home/dockeruser/mount_datasets/20211117-1112/log_0_useful_part.0.log"
    OUTPUT_FILE = "/home/dockeruser/mount_datasets/20211117-1112/log_0_usefull_part_depthmaps.0.msgpack"
    ONLY = ""
    RANGE = ""
elif log_name == "1140":
    ROCK_LOG_FILE = "/home/dockeruser/mount_datasets/20211117-1140/20211117-1140_usefull_interval.0.log"
    OUTPUT_FILE = "/home/dockeruser/mount_datasets/20211117-1140/20211117-1140_usefull_interval_depthmaps.0.msgpack"
    ONLY = ""
    RANGE = ""
elif log_name == "1205_1_laser_scans":
    ROCK_LOG_FILE = "/home/dockeruser/mount_datasets/20211117-1205/laser_scanner_Logger.0.log"
    OUTPUT_FILE = "/home/dockeruser/mount_datasets/20211117-1205/laser_scanner_Logger_until_2000_laser_scans.0.msgpack"
    ONLY = "--only velodyne.laser_scans"
    RANGE = "--end 2000"
elif log_name == "1205_2_laser_scans":
    ROCK_LOG_FILE = "/home/dockeruser/mount_datasets/20211117-1205/laser_scanner_Logger.0.log"
    OUTPUT_FILE = "/home/dockeruser/mount_datasets/20211117-1205/laser_scanner_Logger_from_2000_until_4000_laser_scans.0.msgpack"
    ONLY = "--only velodyne.laser_scans"
    RANGE = "--start 2000 --end 4000"
elif log_name == "1205_3_laser_scans":
    ROCK_LOG_FILE = "/home/dockeruser/mount_datasets/20211117-1205/laser_scanner_Logger.0.log"
    OUTPUT_FILE = "/home/dockeruser/mount_datasets/20211117-1205/laser_scanner_Logger_from_4000_laser_scans.0.msgpack"
    ONLY = "--only velodyne.laser_scans"
    RANGE = "--start 4000"



cmd = "pocolog2msgpack -l %s %s %s -o %s" % (ROCK_LOG_FILE, ONLY, RANGE, OUTPUT_FILE)
print("Command: " + cmd)
proc = pexpect.spawn(cmd, timeout=300)
proc.expect(pexpect.EOF)