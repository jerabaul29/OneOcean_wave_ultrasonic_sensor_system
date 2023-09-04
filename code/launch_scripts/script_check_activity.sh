#!/bin/bash

# to be started from THIS location

echo "----"
date

echo "called from cron, i.e. follows a bootup"

# first, sleep for 1 hour, to give a chance for the first dump to take place after the current reboot
echo "start by sleeping..."
sleep 3600

# then, check periodically that there are some data in
while :
do
    echo "--"
    date
    echo "check activity"
    df -h

    lastModificationSeconds=$(date +%s -r ../../data/last_written.txt)
    currentSeconds=$(date +%s)
    elapsedSeconds=$((currentSeconds - lastModificationSeconds))
    echo "elapsedSeconds since last touch to file: $elapsedSeconds"

    # if there is not file for more than over 0.5 hours, we have a problem
    if [ "$elapsedSeconds" -gt "2000" ]; then
        echo "no logging activity for too long time, reboot"
        sudo reboot -f
    fi

    sleep 1800
done

# if we ever hit the end of this file, something has gone seriously wrong, reboot
sudo reboot -f

