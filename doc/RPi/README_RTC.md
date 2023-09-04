# background

The RPi comes without a RTC. When the RPi starts, it looks for a time server. If a time server is available, it sets time. If not, it resumes time counting from the time at the last shutdown. Therefore, when booting a naked RPi without network or time server, there is no way to be confident about the time value.

To avoid this, we add a RTC. Once the RTC is added and correctly installed, the RPi automatically sets the time at boot and keeps in sync with the RTC: nothing more to do, this is transparent on the user.

# suggested RTC models

The RTCs are:

https://wiki.seeedstudio.com/Pi_RTC-DS1307/#install

or

https://wiki.seeedstudio.com/High_Accuracy_Pi_RTC-DS3231/

Both use a 3V CR1225 lithium cell. We recommend using the high accuracy version of course :) .

# working with the RTC

Follow the tutorial here: https://wiki.seeedstudio.com/High_Accuracy_Pi_RTC-DS3231/ (with a couple of minor changes).

```
pi@raspberrypi:~/Git $ git clone https://github.com/Seeed-Studio/pi-hats.git
Cloning into 'pi-hats'...
remote: Enumerating objects: 394, done.
remote: Counting objects: 100% (135/135), done.
remote: Compressing objects: 100% (91/91), done.
remote: Total 394 (delta 66), reused 71 (delta 44), pack-reused 259
Receiving objects: 100% (394/394), 10.28 MiB | 5.49 MiB/s, done.
Resolving deltas: 100% (181/181), done.

pi@raspberrypi:~/Git $ cd pi-hats/tools

pi@raspberrypi:~/Git/pi-hats/tools $ sudo ./install.sh -u rtc_ds3231
Uninstall rtc_ds1307 ...
Uninstall rtc_ds3231 ...
Uninstall adc_ads1115 ...
Enable I2C interface ...
Install rtc_ds3231 ...
Reading package lists... Done
Building dependency tree       
Reading state information... Done
The following packages will be REMOVED:
  fake-hwclock
0 upgraded, 0 newly installed, 1 to remove and 0 not upgraded.
After this operation, 32.8 kB disk space will be freed.

#######################################################
Reboot the system to take a effect of Install/Uninstall
#######################################################
pi@raspberrypi:~/Git/pi-hats/tools $ sudo shutdown -h now
Connection to 10.42.0.108 closed by remote host.
Connection to 10.42.0.108 closed.
```

# a few notes

The RTC setup is not the only thing needed to set up UTC time on the RPi. Remember to:

- raspi-config and set the Localisation option > timezone to UTC
