#!/bin/bash

# to be launched from THIS location

echo "----"
date

cd ../../code/logger_system/rpi_sl_logger
sleep 5

# python3 script_logging.py >> /home/pi/Git/ultrasound_radar_bow_wave_sensor_Statsraad_Lehmkuhl_2021_2022/data/script_logs/log_logging_script.txt
python3 -u script_logging.py

# if the script ever crashes and we come here, it means something went wrong, we need to reboot
sudo reboot -f

