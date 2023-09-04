#!/bin/bash

# to be launched from THIS location

echo "----"
date

cd ../../code/logger_system/rpi_sl_logger
sleep 5

while :
do
    echo "start the processing script; this should happen only once..."
    python3 -u script_processing.py
done

# if the script ever crashes and we come here, it means something went wrong, we need to reboot
sudo reboot -f
