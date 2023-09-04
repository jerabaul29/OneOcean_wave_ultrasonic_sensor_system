The serial ports are available as "files" in ```/dev/tty*```.

In order to list the serial ports available: ```ls /dev/tty*```.

In order to set the baudrate on a serial port in command line: ```stty -F /dev/ttyUSB0 9600```.

In order to take a quick look at what a serial port is "producing": ```cat < /dev/ttyUSB0```.
