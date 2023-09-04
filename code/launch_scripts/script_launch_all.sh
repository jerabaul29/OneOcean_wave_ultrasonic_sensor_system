#!/bin/bash

cd /home/pi/Git/ultrasound_radar_bow_wave_sensor_Statsraad_Lehmkuhl_2021_2022/code/launch_scripts/

echo "----------"
date

# wait for a bit of time, to give time to the user to interact with the Pi
echo "wait a bit, to give the user time to interact with the pi if needed"
sleep 100
echo "done sleeping, start the different scripts..."

# start the logging script logging to a file
echo "start the logging script"
(bash script_launch_logging.sh | unbuffer -p tee -a /home/pi/Git/ultrasound_radar_bow_wave_sensor_Statsraad_Lehmkuhl_2021_2022/data/script_logs/log_logging_script.txt &)

# start the processing script logging to a file
echo "start the processing script"
(bash script_launch_processing.sh | unbuffer -p tee -a /home/pi/Git/ultrasound_radar_bow_wave_sensor_Statsraad_Lehmkuhl_2021_2022/data/script_logs/log_processing_script.txt &)

# start the check activity script logging to a file
echo "start the script to check activity"
(bash script_check_activity.sh | unbuffer -p tee -a /home/pi/Git/ultrasound_radar_bow_wave_sensor_Statsraad_Lehmkuhl_2021_2022/data/script_logs/log_activity_script.txt &)

# start the script to perform backup; this is a ugly hack, but but, cannot get udev + systemd to work
echo "start the script to perform backup"
(bash script_perform_backup.sh | unbuffer -p tee -a /home/pi/Git/ultrasound_radar_bow_wave_sensor_Statsraad_Lehmkuhl_2021_2022/data/script_logs/log_backup_script.txt &)

# done launching all scripts
echo "done launching all scripts"

