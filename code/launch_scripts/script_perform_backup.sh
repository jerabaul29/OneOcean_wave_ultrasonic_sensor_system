#!/bin/bash

# to be started from THIS location

echo "----"
date

while :
do
	# wait a tiny bit
	sleep 10

	# where to write error messages
	FILE_ERROR_BACKUP_MSG="/media/usb2/perform_backup_error"

	# check that sdb does exist; should be the case
	if [ -e "/dev/sdb" ]
	then
	    echo "sdb exists"
	else
	    # echo "sdb does not exist, try again later"
	    continue
	fi

	sleep 10

	# check that the volume that was just mounted is a volume that "wants" backup
	if [ -f "/media/usb2/perform_backup" ]; then
	    echo "the file perform_backup is present at root of usb2, continue..."
	else 
	    echo "the file perform_backup is not present at root of usb2, abort..."
	    # need sudo in case ext4...
	    echo "-----" | sudo tee -a "${FILE_ERROR_BACKUP_MSG}"
	    date | sudo tee -a "${FILE_ERROR_BACKUP_MSG}"
	    echo "no perform_backup at root of volume, abort..." | sudo tee -a "${FILE_ERROR_BACKUP_MSG}"
	    sudo umount /media/usb2
	    continue
	fi 

	# check that the volume is of the right kind
	PARTITION_KIND=$(sudo file -s /dev/sdb | cut -d " " -f 5)
	if [[ "${PARTITION_KIND}" == "ext4" ]]
	then
	    echo "the usb key is well in ext4 format"
	else
	    echo "the usb key is not in ext4 format, abort..."
	    # need sudo in case ext4...
	    echo "-----" | sudo tee -a "${FILE_ERROR_BACKUP_MSG}"
	    date | sudo tee -a "${FILE_ERROR_BACKUP_MSG}"
	    echo "expected ext4 format, but drive information is:" | sudo tee -a "${FILE_ERROR_BACKUP_MSG}"
	    sudo file -s /dev/sdb | sudo tee -a "${FILE_ERROR_BACKUP_MSG}"
	    sudo umount /media/usb2
	    continue
	fi

	# perform the copy itself
	echo "perform backup"
	mkdir -p /media/usb2/data_ug_sl_backup
	sudo rsync -avh /home/pi/Git/ultrasound_radar_bow_wave_sensor_Statsraad_Lehmkuhl_2021_2022/data/ /media/usb2/data_ug_sl_backup/

	# unmount
	echo "backup performed, unmount USB HDD"
	sudo umount /media/usb2
	echo "done unmount"

	sleep 60
done
