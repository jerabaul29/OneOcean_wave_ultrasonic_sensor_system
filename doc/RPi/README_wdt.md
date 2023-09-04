Need to ensure the RPi is safe with a watchdog; see: https://diode.io/raspberry%20pi/running-forever-with-the-raspberry-pi-hardware-watchdog-20202/

- Enable the hardware watchdog

```
pi@raspberrypi:~ $ sudo su
root@raspberrypi:/home/pi# echo 'dtparam=watchdog=on' >> /boot/config.txt
root@raspberrypi:/home/pi# exit
exit
pi@raspberrypi:~ $ sudo reboot
```

- Install the watchdog system service

```
sudo apt-get update
sudo apt-get install watchdog
```

- configur ethe watchdog service

```
sudo su
echo 'watchdog-device = /dev/watchdog' >> /etc/watchdog.conf
echo 'watchdog-timeout = 15' >> /etc/watchdog.conf
echo 'max-load-1 = 24' >> /etc/watchdog.conf
exit
```

- enable the service

```
sudo systemctl enable watchdog
sudo systemctl start watchdog
sudo systemctl status watchdog
```

- to test: set up a fork bomb, should reboot of itself :)

```
sudo bash -c ':(){ :|:& };:'
```

# notes

If some specific services go down and cause trouble, it is possible to reboot with the watchdog then too by adding these to the watchdog conf. For example, if the wlan0 interface tends to go down, can do something like:

```
sudo su
echo 'interface = wlan0' >> /etc/watchdog.conf
exit
```
