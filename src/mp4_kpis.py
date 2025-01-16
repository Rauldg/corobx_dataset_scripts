from mp3_kpis import convert_rock_logs, convert_mspack_to_relational, load_all_streams, prune_before_movement, plot_odometry_positions, estimate_traveled_distance, plot_positions_3d, compute_duration, prune_after_movement
from import_odometry import load_odometry_from_json
import inquirer
import os


'''
20230209-154158.0003 
    Estimated traveled distance with odometry: 2.8762199704585223 meters
    Total drive time: 235.915938 seconds
    Total drive time: 3.9319323 minutes
    Average speed: 0.012191715383207903 m/s

20230203-125251.0819

    Estimated traveled distance with odometry: 51.97108472359928 meters
    Total drive time: 1220.109951 seconds
    Total drive time: 20.33516585 minutes
    Average speed: 0.04259541091440478 m/s

log_coyote_02-03-2023_13-22_01-exp3

    Estimated traveled distance with odometry: 31.263807752794328 meters
    Total drive time: 618.233262 seconds
    Total drive time: 10.303887699999999 minutes
    Average speed: 0.05056959836107027 m/s

log_coyote_02-03-2023_13-22_01-exp4

    Estimated traveled distance with odometry: 20.178856773437573 meters
    Total drive time: 329.382793 seconds
    Total drive time: 5.489713216666667 minutes
    Average speed: 0.06126263181403521 m/s

log_coyote_02-09-2023_19-14_18_demo_skylight:
    Estimated traveled distance with odometry: 2.564581719323659 meters
    Total drive time: 235.006856 seconds
    Total drive time: 3.9167809333333334 minutes
    Average speed: 0.010912795324250706 m/s

log_coyote_02-09-2023_19-14_20_demo_teleop:
    Estimated traveled distance with odometry: 132.0252413378151 meters
    Total drive time: 797.442584 seconds
    Total drive time: 13.290709733333333 minutes
    Average speed: 0.16556081150767224 m/s
'''

mag_logs = [
    "log_coyote_02-03-2023_13-22_01-exp3",
    "log_coyote_02-03-2023_13-22_01-exp4",
    "log_coyote_02-09-2023_19-14_18_demo_skylight",
    "log_coyote_02-09-2023_19-14_20_demo_teleop"
]

rock_logs = [
    "20230203-125251.0819", 
    "20230209-154158.0003" # Short trajectory - 3.2m
]
options = rock_logs + mag_logs + ["only_stats"]

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


logs_dir = f"/home/dockeruser/mount_datasets/20250110_corobx_journal/mp4_kpis/{log_name}/"
output_dir = logs_dir + 'msgpacks/'
LOGS_AND_STREAMS_TO_CONVERT = {
    'coyote3_odometry_Logger.0.log': ['coyote3_odometry.odometry_delta_samples', 'coyote3_odometry.odometry_samples']
}

# create the output directory if it does not exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def compute_delta_samples(odometry_df):
    odometry_delta_samples_df = odometry_df.copy()
    odometry_delta_samples_df['position.data.0'] = odometry_df['position.data.0'].diff()
    odometry_delta_samples_df['position.data.1'] = odometry_df['position.data.1'].diff()
    odometry_delta_samples_df['position.data.2'] = odometry_df['position.data.2'].diff()
    return odometry_delta_samples_df

def get_complete_stats():
    complete_stats = {
        "20230209-154158.0003": {
            "traveled_distance": 2.8762199704585223,
            "total_drive_time": 235.915938,
            "average_speed": 0.012191715383207903,
            "mode": "autonomous"
        },
        "20230203-125251.0819": {
            "traveled_distance": 51.97108472359928,
            "total_drive_time": 1220.109951,
            "average_speed": 0.04259541091440478,
            "mode": "remote_controlled"
        },
        "log_coyote_02-03-2023_13-22_01-exp3": {
            "traveled_distance": 31.263807752794328,
            "total_drive_time": 618.233262,
            "average_speed": 0.05056959836107027,
            "mode": "remote_controlled"
        },
        "log_coyote_02-03-2023_13-22_01-exp4": {
            "traveled_distance": 20.178856773437573,
            "total_drive_time": 329.382793,
            "average_speed": 0.06126263181403521,
            "mode": "remote_controlled"
        },
        "log_coyote_02-09-2023_19-14_18_demo_skylight": {
            "traveled_distance": 2.564581719323659,
            "total_drive_time": 235.006856,
            "average_speed": 0.010912795324250706,
            "mode": "autonomous"
        },
        "log_coyote_02-09-2023_19-14_20_demo_teleop": {
            "traveled_distance": 132.0252413378151,
            "total_drive_time": 797.442584,
            "average_speed": 0.16556081150767224,
            "mode": "remote_controlled"
        }
    }
    durations_speeds_remote = []
    durations_speeds_auto = []
    distances_remote = []
    distances_auto = []
    for log_name, stats in complete_stats.items():
        if stats['mode'] == 'remote_controlled':
            distances_remote.append(stats['traveled_distance'])
            durations_speeds_remote.append((stats['total_drive_time'], stats['average_speed']))
        else:
            distances_auto.append(stats['traveled_distance'])
            durations_speeds_auto.append((stats['total_drive_time'], stats['average_speed']))
    remote_total_traveled_distance = sum([distance for distance in distances_remote]) 
    remote_total_average_speed = sum(duration*speed for duration, speed in durations_speeds_remote) / sum(duration for duration, _ in durations_speeds_remote)
    remote_total_drive_time = sum([duration for duration, _ in durations_speeds_remote])    
    auto_total_traveled_distance = sum([distance for distance in distances_auto])   
    auto_total_average_speed = sum(duration*speed for duration, speed in durations_speeds_auto) / sum(duration for duration, _ in durations_speeds_auto)
    auto_total_drive_time = sum([duration for duration, _ in durations_speeds_auto])
    complete_stats['remote_total_traveled_distance'] = remote_total_traveled_distance
    complete_stats['remote_total_average_speed'] = remote_total_average_speed
    complete_stats['auto_total_traveled_distance'] = auto_total_traveled_distance
    complete_stats['auto_total_average_speed'] = auto_total_average_speed
    complete_stats['remote_total_drive_time'] = remote_total_drive_time
    complete_stats['auto_total_drive_time'] = auto_total_drive_time
    return complete_stats


if __name__ == '__main__':
    only_stats = log_name == "only_stats"
    if not only_stats:
        if log_name in mag_logs:
            odometry_df = load_odometry_from_json(logs_dir + "odom/")
            streams_data = {}
            streams_data['coyote3_odometry.odometry_samples'] = odometry_df
            streams_data['coyote3_odometry.odometry_delta_samples'] = compute_delta_samples(odometry_df)
        elif log_name in rock_logs:
            convert_rock_logs(logs_dir, output_dir, LOGS_AND_STREAMS_TO_CONVERT)
            convert_mspack_to_relational(output_dir)
            streams_data = load_all_streams(output_dir, LOGS_AND_STREAMS_TO_CONVERT)
        print("Loaded the following streams in a dictionary:")
        print(streams_data.keys())
        # Prune the streams_data:
        # - Remove all streams before the rover starts moving
        streams_data['coyote3_odometry.odometry_samples'] = compute_duration(streams_data['coyote3_odometry.odometry_samples'])
        if log_name == "20230209-154158.0003":
            pruned_streams_data = prune_before_movement(streams_data, prune_until_second=280)
            pruned_streams_data = prune_after_movement(pruned_streams_data, prune_from_second=516)
        elif log_name == "20230203-125251.0819":
            pruned_streams_data = prune_before_movement(streams_data, prune_until_second=308)
            pruned_streams_data = prune_after_movement(pruned_streams_data)
        elif log_name == "log_coyote_02-03-2023_13-22_01-exp3":
            pruned_streams_data = prune_before_movement(streams_data)
            pruned_streams_data = prune_after_movement(pruned_streams_data, prune_from_second=640)
        elif log_name == "log_coyote_02-09-2023_19-14_18_demo_skylight":
            pruned_streams_data = prune_before_movement(streams_data, prune_until_second=190)
            pruned_streams_data = prune_after_movement(pruned_streams_data, prune_from_second=426)
        elif log_name == "log_coyote_02-09-2023_19-14_20_demo_teleop" or log_name == "log_coyote_02-03-2023_13-22_01-exp4":
            pruned_streams_data = prune_before_movement(streams_data)
            pruned_streams_data = prune_after_movement(pruned_streams_data)

        # - Remove from coyote3_geodesic2cart.local_cartesian_position_out, the ranges where the positionType is not 'RTK_FIXED'
        plot_positions_3d(pruned_streams_data['coyote3_odometry.odometry_samples'], output_dir, name='odometry_positions_3d')   
        plot_odometry_positions(pruned_streams_data['coyote3_odometry.odometry_samples'], output_dir, show=True)
        traveled_distance_odometry = estimate_traveled_distance(pruned_streams_data['coyote3_odometry.odometry_samples'])
        print(f"Estimated traveled distance with odometry: {traveled_distance_odometry} meters")
        total_drive_time = pruned_streams_data['coyote3_odometry.odometry_samples'].index[-1] - pruned_streams_data['coyote3_odometry.odometry_samples'].index[0]   
        # Convert the total drive time to seconds from microseconds
        total_drive_time = total_drive_time/1e6
        print(f"Total drive time: {total_drive_time} seconds")
        print(f"Total drive time: {total_drive_time/60.0} minutes")
        average_speed = traveled_distance_odometry / total_drive_time
        print(f"Average speed: {average_speed} m/s")

    print(f"Full stats:")

    complete_stats = get_complete_stats()

    print(f"Average speed in all the remote control logs: {complete_stats['remote_total_average_speed']} m/s")
    print(f"Traveled distance adding all the remote control logs: {complete_stats['remote_total_traveled_distance']} meters")
    print(f"Total drive time adding all the remote control logs: {complete_stats['remote_total_drive_time']} seconds")

    print(f"Average speed in all the autonomous control logs: {complete_stats['auto_total_average_speed']} m/s")
    print(f"Traveled distance adding all the autonomous control logs: {complete_stats['auto_total_traveled_distance']} meters")
    print(f"Total drive time adding all the autonomous control logs: {complete_stats['auto_total_drive_time']} seconds")