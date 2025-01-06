import pocolog2msgpack
import pexpect
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
LOG_NAME = answers['log_name']

print(f"Selected LOG_NAME: {LOG_NAME}")


if LOG_NAME == "1112_part1":
    ROCK_LOG_FILE = "/home/dockeruser/mount_datasets/20211117-1112/depth_map_converter_slam.0.log"
    OUTPUT_FILE = "/home/dockeruser/mount_datasets/20211117-1112/depth_map_converter_slam_until_2000.0.msgpack"
    INTERVAL = "--end 2000"
    ONLY = "--only /depth_map_converter_slam.cloud"
elif LOG_NAME == "1112_part2":
    ROCK_LOG_FILE = "/home/dockeruser/mount_datasets/20211117-1112/depth_map_converter_slam.0.log"
    OUTPUT_FILE = "/home/dockeruser/mount_datasets/20211117-1112/depth_map_converter_slam_start_at_2000.0.msgpack"
    INTERVAL = "--start 2000"
    ONLY = "--only /depth_map_converter_slam.cloud"
elif LOG_NAME == "1140":
    ROCK_LOG_FILE = "/home/dockeruser/mount_datasets/20211117-1140/depth_map_converter_slam.0.log"
    OUTPUT_FILE = "/home/dockeruser/mount_datasets/20211117-1140/depth_map_converter_slam.0.msgpack"
    INTERVAL = ""
    ONLY = "--only /depth_map_converter_slam.cloud"
elif LOG_NAME == "1205":
    ROCK_LOG_FILE = "/home/dockeruser/mount_datasets/20211117-1205/laser_scanner_Logger.0.log"
    OUTPUT_FILE = "/home/dockeruser/mount_datasets/20211117-1205/laser_scanner_Logger_pointcloud.0.msgpack"
    INTERVAL = ""
    ONLY = "--only depth_map_converter.pointcloud"


cmd = "pocolog2msgpack -l %s %s %s -o %s" % (ROCK_LOG_FILE, ONLY, INTERVAL, OUTPUT_FILE)
print("Command: " + cmd)
proc = pexpect.spawn(cmd, timeout=300)
proc.expect(pexpect.EOF)
# log = msgpack.unpack(open(output, "rb"))
# assert_in("/message_producer.messages", log)
# messages = log["/message_producer.messages"]
# assert_equal(len(messages), 2)
# scan = messages[0]
# assert_equal(scan["time"]["microseconds"], 1501161448845619)
# assert_equal(scan["start_angle"], 0.0)
# assert_equal(scan["angular_resolution"], 0.1)
# assert_equal(scan["speed"], 0.1)
# assert_equal(scan["ranges"][0], 30)
# assert_equal(scan["ranges"][1], 31)
# assert_equal(scan["minRange"], 20)
# assert_equal(scan["maxRange"], 40)
# 
# pocolog2msgpack.convert_pocolog_to_msgpack(ROCK_LOG_FILE, "pointclouds.0.msgpack")

