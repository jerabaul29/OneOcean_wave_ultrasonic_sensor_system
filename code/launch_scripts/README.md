# script_launch_all.sh

This script is to be called by cron to start the logging, processing, and activity check. To launch by cron at startup, simply add the following entry to crontab:

```
https://github.com/jerabaul29/ultrasound_radar_bow_wave_sensor_Statsraad_Lehmkuhl_2021_2022/blob/main/code/rpi_cron_content 
```

# scripts to start at boot through the script_launch_all.sh

- script_check_activity.sh checks that logging is active and, if not, reboot the RPi
- script_launch_logging.sh launch the logging; if it ever fails, something bad happened, reboot the RPi
- script_launch_processing.sh launch the processing; should never fail, if it does, reboot the RPi

# script_launch_backup.sh

This script can automatically check for a USB drive being automounted and ready to receive backup, and perform the backup. To be started from a udev rule. For that:

```
pi@raspberrypi:/etc/udev/rules.d $ touch 10-local.rules
```

And in the new rule, put:

```
ACTION=="add", ENV{DEVTYPE}=="usb_device", RUN+="/bin/bash -c 'exec /home/pi/Git/ultrasound_radar_bow_wave_sensor_Statsraad_Lehmkuhl_2021_2022/code/launch_scripts/script_launch_backup.sh'"
```
