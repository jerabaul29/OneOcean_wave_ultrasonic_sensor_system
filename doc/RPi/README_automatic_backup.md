**Make sure that the drive is compatible with Linux filesystems!!!**. Only drives formatted for **Ext4** will be able to be backed up!!

**NOTE: the proper way should be udev rule + systemd service, but I never managed to get this to work; use a haccky script for now**

## make sure that USB drives get auto mounted

```
sudo apt install usbmount
```

edit PrivateMounts from yes to no:

```
pi@raspberrypi:~ $ sudo vim /lib/systemd/system/systemd-udevd.service
PrivateMounts=no
```

## finding the right auto mounted usv drive

As we always use the same "configuration", we will always have:
- usb0 is the SSD HDD
- usb1 is the Arduino Due
- usb2 is the hdd that gets mounted

## add the udev rule

Need to add the udev rule to execute a script on mount:

```
pi@raspberrypi:/etc/udev/rules.d $ sudo vim 10-local.rules
```

add the udev rule:

```
# ACTION=="add", ENV{DEVTYPE}=="usb_device", RUN+="/bin/bash -c 'exec /home/pi/Git/ultrasound_radar_bow_wave_sensor_Statsraad_Lehmkuhl_2021_2022/code/launch_scripts/script_launch_backup.sh'"
ACTION=="add", ENV{DEVTYPE}=="usb_device", SYSTEMD_WANTS="rsync_backup.service"
```

to install the service:

```
cd /etc/systemd/system
sudo touch rsync_backup.service
```

and put the content in the service:

```
[Unit]
Description=Auto rsync USB

[Service]
ExecStart=/home/pi/Git/ultrasound_radar_bow_wave_sensor_Statsraad_Lehmkuhl_2021_2022/code/launch_scripts/script_perform_backup.sh

[Install]
WantedBy=multi-user.target
```

