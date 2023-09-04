This is the full master setup for the RPI model 4 8GB, with Argon M2 housing, SSD HDD, SD card, RTC. Follow the instructions here to set up a full "probes RPi". This has both own information as well as point to other readmes.

Recommended way to interact: headless, ssh, and synchronize the code between the main repo and the RPi using git, by adding a private key on the RPi to access your github account.

In all the following, we assume that the code will be located at ```/home/pi/Git/ultrasound_radar_bow_wave_sensor_Statsraad_Lehmkuhl_2021_2022``` which is where the repo is cloned. Paths etc are relying on this location.

TODO: move large parts of the readme in separate files

# Bill of materials

TODO: add the relevant links for purchase, price, etc.
TODO: put as a table and show total price.

- Argon One M2
- RPi4 8GB RAM
- SD card
- SSD disk
- high accuracy real time clock

# Steps to set up

Remember, when you work with hardware (the Pi, the case, the SSD drive), to always avoid static electricity discharges! Ideally use a "electrostatic discharge bracelet" at a workstation, or if not available, touch some large, grounded pieces of metal before working, and avoid wearing electrostatic clothes such as some synthetics.

## prepare the case

See the Argon manual; main steps:

- put together the side PCB and the RPi 4
- set up the thermal paste
- set up the power selection jumper to the ```2-3 always on``` position on the top cover part
- either now, or at a later stage, install the SSD drive (remove the small screw, insert it in place, put back the small screw)
- either now, or at a later stage, screw the RPi in place
- either now, or at a later stage, put the 4 screws to seal the whole enclosure (may be worth waiting until the SSD drive has been put in place)
- close the enclosing
- at this stage, providing power through the USB-C should switch everything on

## boot from SD card and SSH from computer

The main steps are to 1) burn the SD card, 2) enable the SSH server for next boot by adding a file, 3) successfully ssh into the RPi, 4) setup the SSH server to be enabled by default, 5) change password; see the explanations at:

https://github.com/jerabaul29/ultrasound_radar_bow_wave_sensor_Statsraad_Lehmkuhl_2021_2022/blob/main/doc/RPi/README_get_started.md

## update all software

Always do a full software update the first time:

```
sudo apt update
sudo apt upgrade
sudo apt autoremove
```

There is very little installed by default; make sure to install basic tools:

```
sudo apt install vim
sudo apt install git
sudo apt install tmux
sudo apt-get install smartmontools
```

## setup the case, boot from ssd and use ssd as main drive

There are several good tutorials; see for example: http://wagnerstechtalk.com/argonone/ https://www.yodeck.com/docs/display/YO/Configure+Argon+1+case+with+Fan+and+Power+Button .

### Main button

The main button can be used to switch on, off, reboot: see the table ```AR1-Chart-1.png``` in this folder.

### Fan and IR drivers and config

To install the drivers for the Argon 1 m.2 case (if you chose another model, look for specific information):

```
curl https://download.argon40.com/argon1.sh | bash 
```

To configure the case:

```
argonone-config
```

For example, to reduce the annoying fan noise for low use, some parameters like this may be reasonable:

```
pi@raspberrypi:~ $ argonone-config
--------------------------------------
Argon One Fan Speed Configuration Tool
--------------------------------------
WARNING: This will remove existing configuration.
Press Y to continue:y
Thank you.

Select fan mode:
  1. Always on
  2. Adjust to temperatures (55C, 60C, and 65C)
  3. Customize behavior
  4. Cancel
NOTE: You can also edit /etc/argononed.conf directly
Enter Number (1-4):2

Please provide fan speeds for the following temperatures:
55C (0-100 only):0   [default is  10]
60C (0-100 only):40  [default is  50]
65C (0-100 only):100 [default is 100]
Configuration updated.
```

To allow long term deployment, may be a good idea to reduce a bit the temperature, but to keep the fan under 100% to reduce wear; something like this may be a good idea:

```
pi@raspberrypi:~ $ argonone-config
--------------------------------------
Argon One Fan Speed Configuration Tool
--------------------------------------
WARNING: This will remove existing configuration.
Press Y to continue:y
Thank you.

Select fan mode:
  1. Always on
  2. Adjust to temperatures (55C, 60C, and 65C)
  3. Customize behavior
  4. Cancel
NOTE: You can also edit /etc/argononed.conf directly
Enter Number (1-4):3

Please provide fan speeds and temperature pairs

Provide minimum temperature (in Celsius) then [ENTER]:5
Provide fan speed for 5C (0-100) then [ENTER]:20
* Fan speed will be set to 20 once temperature reaches 5 C

Provide minimum temperature (in Celsius) then [ENTER]:50
Provide fan speed for 50C (0-100) then [ENTER]:50
* Fan speed will be set to 50 once temperature reaches 50 C

Provide minimum temperature (in Celsius) then [ENTER]:65
Provide fan speed for 65C (0-100) then [ENTER]:100
* Fan speed will be set to 100 once temperature reaches 65 C

Provide minimum temperature (in Celsius) then [ENTER]:

Thank you!  We saved 3 pairs.
Changes should take effect now.
```

There is also possibility to configure the infrared control, through ```argonne-ir```. We will not use it in the present project, so dropping it.

### Use SSD as main bootable drive

TODO: The SD card has low stability and performance, this is why
TODO: put in its own tutorial file?

There are several good tutorials online; see for example https://www.waveshare.com/wiki/PI4-CASE-ARGON-ONE-M.2 .

- First, full update the RPi:

```
sudo apt-get update
sudo apt-get full-upgrade
sudo rpi-update
sudo reboot
sudo rpi-eeprom-update -d -a
sudo reboot
```

- Then, put in place the SSD drive (i.e., power off, remove the small screw, insert the drive, put back the small screw (that's a tough one for big fingers :) ), install the USB jumper outside of the case).

- To check that the SSD disk is well found, try with and without the USB jumper:

```
pi@raspberrypi:/media $ lsusb
Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
Bus 001 Device 002: ID 2109:3431 VIA Labs, Inc. Hub
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
pi@raspberrypi:/media $ lsusb
Bus 002 Device 004: ID 174c:55aa ASMedia Technology Inc. Name: ASM1051E SATA 6Gb/s bridge, ASM1053E SATA 6Gb/s bridge, ASM1153 SATA 3Gb/s bridge, ASM1153E SATA 6Gb/s bridge
Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
Bus 001 Device 002: ID 2109:3431 VIA Labs, Inc. Hub
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
```

You can see that there is a new entry corresponding to the SSD disk.

- The, set it up for booting:

```
sudo raspi-config
# there: Advanced options > Boot order > B2 USB boot and ENTER to confirm
# then finish without rebooting
```

- At this stage, need to clone the SD card into the SSD disk. Note: if not doing so the RPi will fail to boot, as it will try to boot from the empty SSD disk; to remedy this, in case the SSD disk has not been cloned yet but you want to reboot, simply remove the USB jumper before rebooting, and the SSD disk will not be available, so that the RPi will default to booting on the SD card.

To clone, since we do not have a GUI environment, we follow the instructions at https://www.raspberrypi.org/forums/viewtopic.php?t=180383 , which lead to using the code on the repo https://github.com/billw2/rpi-clone .

- To install rpi-clone:

```
pi@raspberrypi:/ $ cd home/pi/
pi@raspberrypi:~ $ mkdir Git
pi@raspberrypi:~ $ cd Git/
pi@raspberrypi:~/Git $ git clone https://github.com/billw2/rpi-clone.git
pi@raspberrypi:~/Git $ cd rpi-clone/
pi@raspberrypi:~/Git/rpi-clone $ sudo cp rpi-clone rpi-clone-setup /usr/local/sbin
pi@raspberrypi:~/Git/rpi-clone $ sudo rpi-clone-setup -t testhostname
```

- To use rpi-clone: find the destination on which to clone, and run the command. This will both clone the boot and the "normal" partitions, and resize them to take advantage of the full disk.

```
pi@raspberrypi:~/Git/rpi-clone $ lsblk
NAME        MAJ:MIN RM   SIZE RO TYPE MOUNTPOINT
sda           8:0    0 223.6G  0 disk 
mmcblk0     179:0    0  14.9G  0 disk 
|-mmcblk0p1 179:1    0   256M  0 part /boot
`-mmcblk0p2 179:2    0  14.6G  0 part /
pi@raspberrypi:~/Git/rpi-clone $ sudo rpi-clone sda
Error: /dev/sda: unrecognised disk label

Booted disk: mmcblk0 15.9GB                Destination disk: sda 240.1GB
---------------------------------------------------------------------------
Part      Size    FS     Label           Part   Size  FS  Label
1 /boot   256.0M  fat32  --                                 
2 root     14.6G  ext4   rootfs                             
---------------------------------------------------------------------------
== Initialize: IMAGE partition table - partition number mismatch: 2 -> 0 ==
1 /boot               (47.5M used)   : MKFS  SYNC to sda1
2 root                (1.4G used)    : RESIZE  MKFS  SYNC to sda2
---------------------------------------------------------------------------
Run setup script       : no.
Verbose mode           : no.
-----------------------:
** WARNING **          : All destination disk sda data will be overwritten!
-----------------------:

Initialize and clone to the destination disk sda?  (yes/no): yes
Optional destination ext type file system label (16 chars max): 

Initializing
  Imaging past partition 1 start.
  => dd if=/dev/mmcblk0 of=/dev/sda bs=1M count=8 ...
  Resizing destination disk last partition ...
    Resize success.
  Changing destination Disk ID ...
  => mkfs -t vfat -F 32  /dev/sda1 ...
  => mkfs -t ext4  /dev/sda2 ...

Syncing file systems (can take a long time)
Syncing mounted partitions:
  Mounting /dev/sda2 on /mnt/clone
  => rsync // /mnt/clone with-root-excludes ...
  Mounting /dev/sda1 on /mnt/clone/boot
  => rsync /boot/ /mnt/clone/boot  ...

Editing /mnt/clone/boot/cmdline.txt PARTUUID to use c330f0f5
Editing /mnt/clone/etc/fstab PARTUUID to use c330f0f5
===============================
Done with clone to /dev/sda
   Start - 08:38:23    End - 08:39:42    Elapsed Time - 1:19

Cloned partitions are mounted on /mnt/clone for inspection or customizing. 

Hit Enter when ready to unmount the /dev/sda partitions ...
  unmounting /mnt/clone/boot
  unmounting /mnt/clone
===============================
```

If you want to inspect the content of it, create a mounting point and mount:

```
pi@raspberrypi:/ $ sudo mkdir mnt/sda_disk_1
pi@raspberrypi:/ $ sudo mkdir mnt/sda_disk_2
pi@raspberrypi:/ $ sudo mount /dev/sda1 /mnt/sda_disk_1/
pi@raspberrypi:/ $ sudo mount /dev/sda2 /mnt/sda_disk_2/
```

At this stage, we should have 1) by default, boot from the USB SSD drive external storage, 2) cloned both partitions of the SD card into the SSD drive to make it bootable and usable as the main drive. So, we are ready to reboot, and the boot will happen from the SSD drive this time :) . This is confirmed by:

```
pi@raspberrypi:~ $ sudo reboot now
Connection to 10.42.0.105 closed by remote host.
Connection to 10.42.0.105 closed.
~$ ssh pi@10.42.0.105
pi@10.42.0.105's password: 
Linux raspberrypi 5.10.17-v7l+ #1421 SMP Thu May 27 14:00:13 BST 2021 armv7l

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
Last login: Thu Jun  3 08:19:33 2021 from 10.42.0.1

Wi-Fi is currently blocked by rfkill.
Use raspi-config to set the country before use.

pi@raspberrypi:~ $ df -h
Filesystem      Size  Used Avail Use% Mounted on
/dev/root       219G  1.5G  207G   1% /
devtmpfs        3.8G     0  3.8G   0% /dev
tmpfs           3.9G     0  3.9G   0% /dev/shm
tmpfs           3.9G  8.5M  3.9G   1% /run
tmpfs           5.0M  4.0K  5.0M   1% /run/lock
tmpfs           3.9G     0  3.9G   0% /sys/fs/cgroup
/dev/sda1       253M   48M  205M  19% /boot
tmpfs           788M     0  788M   0% /run/user/1000
```

I.e. now the main drive ```/dev/root``` has a totale size around 220GB, which is (except for the overheads, partition table, boot partition) the size of the SSD drive. You can remove the SD card. Remember that the device will not boot without the USB jumper!

## setup RTC

The RPi comes without a RTC, and we need to set all to UTC to make time referencing easy. See: https://github.com/jerabaul29/ultrasound_radar_bow_wave_sensor_Statsraad_Lehmkuhl_2021_2022/blob/main/doc/RPi/README_RTC.md .

On the Argon One m2 case, the pins are broken out on the top of the RPi (remove the magnetic top panel to access these). The RTC needs to be installed on the very left of the broken out pins, pointing downwards, to fit the pinout mapping.

## setup WDT

We want to make sure a kernel / hardware crash or similar will be caught and lead to reboot, rather than freeze the whole device. See https://github.com/jerabaul29/ultrasound_radar_bow_wave_sensor_Statsraad_Lehmkuhl_2021_2022/blob/main/doc/RPi/README_wdt.md .

## software installation for the logger

## network setup

From a message from the responsible for the network on board:

"

This is an IPv4 network, you can use the static IP 10.42.1.55. Other information about the network:

Range:
- 10.42.1.0/24 GW: n/a
- DNS: 10.42.1.10
- DHCP range: 10.42.1.101-200

"

TODO: on the boat, set the IP addresses as they want if relevant; see for example https://www.ionos.com/digitalguide/server/configuration/provide-raspberry-pi-with-a-static-ip-address/ https://thepihut.com/blogs/raspberry-pi-tutorials/how-to-give-your-raspberry-pi-a-static-ip-address-update https://www.raspberrypi.org/documentation/configuration/tcpip/ https://pimylifeup.com/raspberry-pi-static-ip-address/

## monitoring the RPi

- temperature of the GPU and CPU:

```
pi@raspberrypi:~ $ vcgencmd measure_temp
temp=35.0'C
pi@raspberrypi:~ $ cpu=$(</sys/class/thermal/thermal_zone0/temp)
pi@raspberrypi:~ $ echo "$((cpu/1000)) c"
36 c
```

- temperature of the SSD drive:

```
pi@raspberrypi:~ $ sudo smartctl -x /dev/sda | grep 'Temperature'
194 Temperature_Celsius     -O---K   053   048   000    -    47 (Min/Max 10/48)
0x05  =====  =               =  ===  == Temperature Statistics (rev 1) ==
0x05  0x008  1              47  ---  Current Temperature
0x05  0x010  1               -  ---  Average Short Term Temperature
0x05  0x018  1               -  ---  Average Long Term Temperature
0x05  0x020  1              47  ---  Highest Temperature
0x05  0x028  1              41  ---  Lowest Temperature
0x05  0x030  1               -  ---  Highest Average Short Term Temperature
0x05  0x038  1               -  ---  Lowest Average Short Term Temperature
0x05  0x040  1               -  ---  Highest Average Long Term Temperature
0x05  0x048  1               -  ---  Lowest Average Long Term Temperature
0x05  0x050  4               0  ---  Time in Over-Temperature
0x05  0x058  1              95  ---  Specified Maximum Operating Temperature
0x05  0x060  4               0  ---  Time in Under-Temperature
0x05  0x068  1               0  ---  Specified Minimum Operating Temperature
```

## setup of master startup script

```
$ crontab -e
$ mkdir -p /home/pi/Git/ultrasound_radar_bow_wave_sensor_Statsraad_Lehmkuhl_2021_2022/data/script_logs/
```

Then add line:

```
@reboot bash /home/pi/Git/ultrasound_radar_bow_wave_sensor_Statsraad_Lehmkuhl_2021_2022/code/launch_scripts/script_launch_all.sh >> /home/pi/Git/ultrasound_radar_bow_wave_sensor_Statsraad_Lehmkuhl_2021_2022/data/script_logs/log_script_launch_all.txt
```

## Static IP network for deployment on the boat

See: https://github.com/jerabaul29/ultrasound_radar_bow_wave_sensor_Statsraad_Lehmkuhl_2021_2022/blob/main/doc/RPi/README_network_and_broadcast.md . A small tips: do this when you have physical access to the RPi and have screen and keyboard, as this will be the only way to access it if you lock yourself out of ssh by mis configurating the network.
