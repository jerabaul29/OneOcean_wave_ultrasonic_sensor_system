# preparing a new sd card on an Ubuntu computer

- The image is downloaded from https://www.raspberrypi.org/software/operating-systems/ (Raspbian download OS images)
- I recommend downloading and using the ```Raspberry Pi OS Lite```
- There are problems unzipping large files using the GUI; to unzip using the command line:
```
~/Desktop/Software/RaspberryPi/image_june_2021$ unzip 2021-05-07-raspios-buster-armhf-lite.zip 
Archive:  2021-05-07-raspios-buster-armhf-lite.zip
  inflating: 2021-05-07-raspios-buster-armhf-lite.img  
```
- The image is burnt to the RPi with rpi-imager (installed from snap on Ubuntu)
```
~/Desktop/Software/RaspberryPi/image_june_2021$ sudo snap install rpi-imager
[sudo] password for jrmet: 
... installing ...
~/Desktop/Software/RaspberryPi/image_june_2021$ rpi-imager
```

# making the RPi available for SSH-ing

- Add a ```ssh``` file on the boot partition to enable ssh (which is diabled by default)

NOTE: the ssh file will be removed at each reboot!!! You will need to put it by hand again and again if not doing the following ssh server activation!
NOTE: the rpi user is ```pi```, the default password is ```raspberry```

- in order to set up the SSH option to open for all time following (note: this can be made through SSH after logging the first time in headless mode by adding the ssh file), ssh into the RPi (see help in the next section), and set up the ssh server to start at boot automatically:
    - ```pi@raspberrypi:~ $ sudo raspi-config```
    - In the interactive menu, go to Interface Options > SSH > Yes > Ok > Finish
    - Now, the ssh server should be available also after reboot

- if SSH gets enabled, make sure to change the default password, otherwise this is a security risk! The password we usually use for the RPi controlling the probes system on a protected network is: ```raspberry_ug_sl```. To change the password, the command is:

```pi@raspberrypi:~ $ passwd```

# ssh-ing to the RPi

- connect with an ethernet cable

- on Ubuntu 20.04, need to set up a new profile for the ethernet connection:
    - network manager > Wired settings > +
    - create a RPi profile
    - in this profile, use "shared to other computers" for the IPv4 and IPv6

- find out the ssh address of the RPi. This is a bit of work:

before the RPi is plugged in, I only have WiFi IP:

```
~$ ifconfig
enp0s31f6: flags=4099<UP,BROADCAST,MULTICAST>  mtu 1500       <<<<<<<<<<<< not in use so far (this is my Wired interface)
        ether f8:75:a4:f3:9f:6d  txqueuelen 1000  (Ethernet)
        RX packets 389  bytes 43966 (43.9 KB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 1220  bytes 115561 (115.5 KB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
        device interrupt 16  memory 0xa1400000-a1420000  

lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536
        inet 127.0.0.1  netmask 255.0.0.0
        inet6 ::1  prefixlen 128  scopeid 0x10<host>
        loop  txqueuelen 1000  (Local Loopback)
        RX packets 67750  bytes 6173443 (6.1 MB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 67750  bytes 6173443 (6.1 MB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

wlp5s0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 192.168.0.12  netmask 255.255.255.0  broadcast 192.168.0.255
        inet6 fe80::3610:c888:2de0:e163  prefixlen 64  scopeid 0x20<link>
        ether 04:33:c2:b3:bf:55  txqueuelen 1000  (Ethernet)
        RX packets 2419690  bytes 1794180449 (1.7 GB)
        RX errors 0  dropped 2  overruns 0  frame 0
        TX packets 665914  bytes 434975130 (434.9 MB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
```

After the RPi is plugged in, and with SSH activated, I have both WiFi and Wired IP:

```
 ~$ ifconfig
enp0s31f6: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.42.0.1  netmask 255.255.255.0  broadcast 10.42.0.255      <<<<<<<<< NOTE THIS NEW LINE!! IP of the computer on the Wired interface
        inet6 fe80::582e:96b3:9c18:8bc1  prefixlen 64  scopeid 0x20<link>
        ether f8:75:a4:f3:9f:6d  txqueuelen 1000  (Ethernet)
        RX packets 414  bytes 48048 (48.0 KB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 1266  bytes 123436 (123.4 KB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
        device interrupt 16  memory 0xa1400000-a1420000  

lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536
        inet 127.0.0.1  netmask 255.0.0.0
        inet6 ::1  prefixlen 128  scopeid 0x10<host>
        loop  txqueuelen 1000  (Local Loopback)
        RX packets 68821  bytes 6269698 (6.2 MB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 68821  bytes 6269698 (6.2 MB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

wlp5s0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 192.168.0.12  netmask 255.255.255.0  broadcast 192.168.0.255
        inet6 fe80::3610:c888:2de0:e163  prefixlen 64  scopeid 0x20<link>
        ether 04:33:c2:b3:bf:55  txqueuelen 1000  (Ethernet)
        RX packets 2463028  bytes 1815509964 (1.8 GB)
        RX errors 0  dropped 2  overruns 0  frame 0
        TX packets 671592  bytes 436046259 (436.0 MB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
```

At this stage, need to scan the IPs on the Wired network. For this, use the IP on the wired network (here, 10.42.0.1), and scan the adresses there:

```
~$ nmap -sn 10.42.0.0/24
Starting Nmap 7.80 ( https://nmap.org ) at 2021-04-15 13:49 CEST
Nmap scan report for jrmet-ThinkPad-L590 (10.42.0.1)
Host is up (0.00044s latency).
Nmap scan report for 10.42.0.108
Host is up (0.00093s latency).
Nmap done: 256 IP addresses (2 hosts up) scanned in 2.55 seconds
```

The address we need is the "extra" one; here: ```10.42.0.108```. Once this address is found, ssh-ing is easy; the user to use for logging is ```pi```, so for example in this case the ssh command is:

```ssh pi@10.42.0.108```

In order to be able to display windows if needed, use the -X option: ```ssh -X pi@YOUR_IP``` .

# diverse

The Rpi is a "normal" Linux computer. It can also be accessed through the screen, keyboard, mouse etc by pugging these in the Pi if needed for first time users :) .
