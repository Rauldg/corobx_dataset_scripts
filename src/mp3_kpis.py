'''
1 convert the mp3 rock logs to msgpack format. The needed streams are:
- Odometry, coyote3_odometry_Logger.0.log:
    - coyote3_odometry.odometry_delta_samples
    - coyote3_odometry.odometry_samples
- GPS,  coyote3_sensor_base_deployment_Logger.0.log:
    - coyote3_imu.gps_solution
    - coyote3_geodesic2cart.local_cartesian_position_out
- Winch command, in coyote3_guidance_rappel_Logger.0.log:
    - coyote3_guidance_rappel.winch_commands
'''
import pexpect
import os
import sys
import msgpack
import pandas as pd
import pocolog2msgpack
import matplotlib.pyplot as plt

LOGS_DIR = '/home/dockeruser/mount_datasets/20250107_corobx_journal/mp3_kpis/20230209-135322.0333/'
OUTPUT_DIR = LOGS_DIR + 'msgpacks/'
LOGS_AND_STREAMS_TO_CONVERT = {
    'coyote3_odometry_Logger.0.log': ['coyote3_odometry.odometry_delta_samples', 'coyote3_odometry.odometry_samples'],
    'coyote3_sensor_base_deployment_Logger.0.log': ['coyote3_imu.gps_solution', 'coyote3_geodesic2cart.local_cartesian_position_out'],
    'coyote3_guidance_rappel_Logger.0.log': ['coyote3_guidance_rappel.winch_commands']
}



def convert_rock_logs(logs_dir, output_dir, logs_and_streams_to_convert):
    # Create the output directory if it does not exist
    os.makedirs(output_dir, exist_ok=True)
    for log, streams in logs_and_streams_to_convert.items():
        rock_log_file = logs_dir + log
        for stream in streams:
            output_file = output_dir + log.replace('.0.log', '.0.%s.msgpack'%stream)
            # Check if the file already exists
            if os.path.exists(output_file):
                print(f"File {output_file} already exists. Skipping the convertion ...")
            else:
                only = ' --only %s'%stream
                cmd = "pocolog2msgpack -l %s %s -o %s" % (rock_log_file, only, output_file)
                full_cmd = f"source /opt/workspace/env.sh; {cmd}"
                print("Command: " + full_cmd)
                proc = pexpect.spawn('/bin/bash', ['-c', full_cmd], timeout=300)
                # Capture and print the output
                proc.logfile_read = sys.stdout.buffer
                proc.expect(pexpect.EOF)
                proc.close()

def convert_mspack_to_relational(msgpack_dir):
    # For each log file in msgpack_dir, convert it to relational format
    for logfile in os.listdir(msgpack_dir):
        if logfile.endswith('.msgpack'):
            # Check if the corresponing relational file already exists
            if os.path.exists(msgpack_dir + logfile.replace('.msgpack', '.relational')):
                print(f"File {logfile.replace('.msgpack', '.relational')} already exists. Skipping the convertion ...")
            else:
                logfile_relational = msgpack_dir + logfile.replace('.msgpack', '.relational')
                pocolog2msgpack.object2relational(msgpack_dir + logfile, logfile_relational, whitelist=['position.data'])

def load_all_streams(output_dir, logs_and_streams_to_convert):
    streams_data = {}
    for log, streams in logs_and_streams_to_convert.items():
        for stream in streams:
            msgpack_file = output_dir + log.replace('.0.log', '.0.%s.relational'%stream)
            log_data = msgpack.unpack(open(msgpack_file, "rb"))    
            df = pd.DataFrame(log_data[stream])
            df.set_index("timestamp", inplace=True)
            streams_data[stream] = df
    return streams_data

#def plot_solution_vs_time(streams_data):
#    solution = streams_data['coyote3_imu.gps_solution']
#    solution['positionType'] = solution['positionType'].astype('category')
#    solution['solution_code'] = solution['positionType'].cat.codes
#    plt.figure(figsize=(10, 6))
#    plt.plot(solution.index, solution['solution_code'], marker='o', linestyle='-', label='Solution')
#    plt.xlabel('Timestamp')
#    plt.ylabel('Solution')
#    plt.title('Solution vs. Timestamp')
#    plt.legend()
#    plt.grid(True)
#    
#    # Set y-tick labels to category names
#    unique_codes = solution['solution_code'].unique()
#    unique_labels = solution['positionType'].cat.categories[unique_codes]
#    plt.yticks(ticks=unique_codes, labels=unique_labels)
# 
#    #plt.show()
#    # Save the plot
#    plt.savefig(OUTPUT_DIR + 'solution_vs_time.png')

def plot_solution_vs_time(streams_data):
    solution = streams_data['coyote3_imu.gps_solution']
    solution['positionType'] = solution['positionType'].astype('category')
    solution['solution_code'] = solution['positionType'].cat.codes

    #plt.figure(figsize=(10, 6))

    # Plot rectangles for each solution type
    for code in solution['solution_code'].unique():
        mask = solution['solution_code'] == code
        plt.broken_barh(
            [(start, end - start) for start, end in zip(solution.index[:-1], solution.index[1:]) if mask[start]],
            (plt.gca().get_ylim()[0], plt.gca().get_ylim()[1] - plt.gca().get_ylim()[0]),
            facecolors=plt.cm.tab20(code / len(solution['solution_code'].unique())),
            alpha=0.5,
            label=solution['positionType'].cat.categories[code]
        )

    plt.xlabel('Timestamp')
    plt.title('Solution vs. Timestamp')
    plt.legend()
    plt.grid(True)

    # Save the plot
    plt.savefig(OUTPUT_DIR + 'solution_vs_time.png')


def prune_before_movement(streams_data, prune_until_second=None):
    odometry_delta = streams_data['coyote3_odometry.odometry_delta_samples']
    # Find the first timestamp when the rover starts moving
    first_movement = odometry_delta[odometry_delta['position.data.0'] > 0].index[0]
    pruned_streams_data = {}
    for stream, df in streams_data.items():
        pruned_streams_data[stream] = df[df.index >= first_movement]
    if prune_until_second:
        odometry = streams_data['coyote3_odometry.odometry_samples']
        prune_until_timestamp = odometry[odometry['duration_seconds'] > prune_until_second].index[0]
        for stream, df in pruned_streams_data.items():
            pruned_streams_data[stream] = df[df.index > prune_until_timestamp]
    return pruned_streams_data

def prune_after_movement(streams_data, prune_from_second=None):
    odometry_delta = streams_data['coyote3_odometry.odometry_delta_samples']
    # Find the last timestamp when the rover was moving
    last_movement = odometry_delta[odometry_delta['position.data.0'] > 0].index[-1]
    pruned_streams_data = {}
    for stream, df in streams_data.items():
        pruned_streams_data[stream] = df[df.index <= last_movement]
    if prune_from_second:
        odometry = streams_data['coyote3_odometry.odometry_samples']
        prune_from_timestamp = odometry[odometry['duration_seconds'] > prune_from_second].index[0]
        for stream, df in pruned_streams_data.items():
            pruned_streams_data[stream] = df[df.index < prune_from_timestamp]
    return pruned_streams_data

def plot_odometry_positions(odometry_df, output_dir, show=False):
    plt.figure(figsize=(10, 6))
    
    plt.plot(odometry_df['duration_seconds'], odometry_df['position.data.0'], marker='o', linestyle='-', label='X')
    plt.plot(odometry_df['duration_seconds'], odometry_df['position.data.1'], marker='o', linestyle='-', label='Y')
    plt.plot(odometry_df['duration_seconds'], odometry_df['position.data.2'], marker='o', linestyle='-', label='Z')
    plt.xlabel('Duration (s)')
    plt.ylabel('Position (m)')
    plt.title('Odometry Position vs. Duration')
    plt.legend()
    plt.grid(True)
    if show:
        plt.show()
    # Save the plot
    plt.savefig(output_dir + 'odometry_positions_time.png')

def plot_local_cartesian_positions(local_cartesian_gps_df):
    plt.figure(figsize=(10, 6))
    local_cartesian_gps_df['timestamps_seconds'] = local_cartesian_gps_df.index / 1e6
    local_cartesian_gps_df['duration_seconds'] = local_cartesian_gps_df['timestamps_seconds'] - local_cartesian_gps_df['timestamps_seconds'].iloc[0]
    plt.plot(local_cartesian_gps_df['duration_seconds'], local_cartesian_gps_df['position.data.0'], marker='o', linestyle='-', label='X')
    plt.plot(local_cartesian_gps_df['duration_seconds'], local_cartesian_gps_df['position.data.1'], marker='o', linestyle='-', label='Y')
    plt.plot(local_cartesian_gps_df['duration_seconds'], local_cartesian_gps_df['position.data.2'], marker='o', linestyle='-', label='Z')
    plt.xlabel('Timestamp')
    plt.ylabel('Position')
    plt.title('Local Cartesian GPS Positions vs. Timestamp')
    plt.legend()
    plt.grid(True)
    #plt.show()
    # Save the plot
    plt.savefig(OUTPUT_DIR + 'local_cart_gps_positions_time.png')

def estimate_traveled_distance(local_cartesian_gps_df):
    # Compute the traveled distance in meters
    delta_x = local_cartesian_gps_df['position.data.0'].diff()
    delta_y = local_cartesian_gps_df['position.data.1'].diff()
    delta_z = local_cartesian_gps_df['position.data.2'].diff()
    distance = (delta_x**2 + delta_y**2 + delta_z**2)**0.5
    traveled_distance = distance.sum()
    return traveled_distance

def prune_not_rtk_fixed(streams_data):
    gps_solution = streams_data['coyote3_imu.gps_solution']
    gps_solution['positionType'] = gps_solution['positionType'].astype('category')
    gps_solution['solution_code'] = gps_solution['positionType'].cat.codes
    # Find the ranges where the positionType is not 'RTK_FIXED'
    not_rtk_fixed = gps_solution[gps_solution['positionType'] != 'RTK_FIXED']
    if not not_rtk_fixed.empty:
        first_not_rtk_fixed_index = not_rtk_fixed.index[0]
        df = streams_data['coyote3_geodesic2cart.local_cartesian_position_out']
        streams_data['coyote3_geodesic2cart.local_cartesian_position_out'] = df[df.index < first_not_rtk_fixed_index]
    return streams_data

def plot_positions_3d(positions_df, output_dir, name='local_cart_gps_positions_3d'):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(positions_df['position.data.0'], positions_df['position.data.1'], positions_df['position.data.2'])
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    plt.show()
    plt.savefig(output_dir + '%s.png'%name)

def compute_duration(df):
    df['timestamps_seconds'] = df.index / 1e6
    df['duration_seconds'] = df['timestamps_seconds'] - df['timestamps_seconds'].iloc[0]
    return df

if __name__ == '__main__':
    convert_rock_logs(LOGS_DIR, OUTPUT_DIR, LOGS_AND_STREAMS_TO_CONVERT)
    convert_mspack_to_relational(OUTPUT_DIR)
    streams_data = load_all_streams(OUTPUT_DIR, LOGS_AND_STREAMS_TO_CONVERT)
    print("Loaded the following streams in a dictionary:")
    print(streams_data.keys())
    # Prune the streams_data:
    # - Remove all streams before the rover starts moving
    pruned_streams_data = prune_before_movement(streams_data)
    pruned_streams_data['coyote3_odometry.odometry_samples'] = compute_duration(pruned_streams_data['coyote3_odometry.odometry_samples'])
    pruned_streams_data = prune_after_movement(pruned_streams_data, prune_from_second=492)
    # - Remove from coyote3_geodesic2cart.local_cartesian_position_out, the ranges where the positionType is not 'RTK_FIXED'
    pruned_streams_data = prune_not_rtk_fixed(pruned_streams_data)
    plot_positions_3d(pruned_streams_data['coyote3_geodesic2cart.local_cartesian_position_out'], OUTPUT_DIR)
    plot_positions_3d(pruned_streams_data['coyote3_odometry.odometry_samples'], OUTPUT_DIR, name='odometry_positions_3d')   
    plot_local_cartesian_positions(pruned_streams_data['coyote3_geodesic2cart.local_cartesian_position_out'])
    plot_odometry_positions(pruned_streams_data['coyote3_odometry.odometry_samples'], OUTPUT_DIR)
    plot_solution_vs_time(pruned_streams_data)
    traveled_distance = estimate_traveled_distance(pruned_streams_data['coyote3_geodesic2cart.local_cartesian_position_out'])
    print(f"Estimated traveled distance with RTK_FIXED precision: {traveled_distance} meters")
    traveled_distance_odometry = estimate_traveled_distance(pruned_streams_data['coyote3_odometry.odometry_samples'])
    print(f"Estimated traveled distance with odometry: {traveled_distance_odometry} meters")
    total_drive_time = pruned_streams_data['coyote3_odometry.odometry_samples'].index[-1] - pruned_streams_data['coyote3_odometry.odometry_samples'].index[0]   
    # Convert the total drive time to seconds from microseconds
    total_drive_time = total_drive_time/1e6
    print(f"Total drive time: {total_drive_time} seconds")
    print(f"Total drive time: {total_drive_time/60.0} minutes")
    average_speed = traveled_distance_odometry / total_drive_time
    print(f"Average speed: {average_speed} m/s")    