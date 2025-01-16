import inquirer
from mp3_kpis import plot_odometry_positions, compute_duration, plot_positions_3d
import os
import json
import pandas as pd

def load_odometry_from_json(log_folder):
    '''
    for each file in log_folder, load the odometry data from the json file

    The odometry file format is this one:

    {
	"data" : 
	{
		"covariance" : 
		[
			[ 1.0000000000000001e-05, 0, 0, 0, 0, 0 ],
			[ 0, 1.0000000000000001e-05, 0, 0, 0, 0 ],
			[ 0, 0, 1.0000000000000001e-05, 0, 0, 0 ],
			[ 0, 0, 0, 1.0000000000000001e-05, 0, 0 ],
			[ 0, 0, 0, 0, 1.0000000000000001e-05, 0 ],
			[ 0, 0, 0, 0, 0, 1.0000000000000001e-05 ]
		],
		"orientation" : 
		{
			"w" : 0.72313759467623995,
			"x" : 0.011516361741657252,
			"y" : 0.0075339543666338863,
			"z" : -0.69056689184299802
		},
		"translation" : [ -0.0002143961645848341, 0.0023562405776185852, 4.5836502710967155e-06 ]
	},
	"metadata" : 
	{
		"childTime" : 
		{
			"microseconds" : 1675429069933564
		},
		"childframeId" : "",
		"dataEstimated" : [ true, true, true, true, true, true, true ],
		"msgVersion" : 1,
		"parentTime" : 
		{
			"microseconds" : 1675429069933564
		},
		"parentframeId" : "",
		"producerId" : "Odometry"
	}
    }
    '''

    

    data = []
    for file in os.listdir(log_folder):
        if file.endswith(".json"):
            with open(os.path.join(log_folder, file)) as f:
                odometry = json.load(f)
                timestamp = file.split(".")[0]
                timestamp = timestamp.split("_")[1]
                timestamp = int(timestamp)
                data.append({
                    "timestamp": timestamp,
                    "covariance": odometry["data"]["covariance"],
                    "orientation": odometry["data"]["orientation"],
                    "translation": odometry["data"]["translation"],
                    "metadata": odometry["metadata"]
                })

    odometry_df = pd.DataFrame(data)
    odometry_df = odometry_df.set_index("timestamp")
    # order by the index
    odometry_df = odometry_df.sort_index()
    # divide the translation into position.data.0, position.data.1 and position.data.2
    odometry_df["position.data.0"] = odometry_df["translation"].apply(lambda x: x[0])
    odometry_df["position.data.1"] = odometry_df["translation"].apply(lambda x: x[1])
    odometry_df["position.data.2"] = odometry_df["translation"].apply(lambda x: x[2])
    odometry_df = odometry_df.drop(columns=["translation"])
    return odometry_df


if __name__ == '__main__':
	log_name = "log_coyote_02-03-2023_13-22_01-exp3"
	
	# Example usage
	log_folder = f"/home/dockeruser/mount_datasets/20250110_corobx_journal/mp4_kpis/{log_name}/odom/"
	odometry = load_odometry_from_json(log_folder)
	output_folder = log_folder + 'plots/'
	
	# if the output_dir does not exist, create it
	if not os.path.exists(output_folder):
		os.makedirs(output_folder)
	
	odometry = compute_duration(odometry)
	
	
	# Prune after second 640
	prune_from_second = 640
	prune_from_timestamp = odometry[odometry['duration_seconds'] > prune_from_second].index[0]
	odometry = odometry[odometry.index < prune_from_timestamp]
	
	
	plot_odometry_positions(odometry, output_folder, show=False)
	plot_positions_3d(odometry, output_folder)