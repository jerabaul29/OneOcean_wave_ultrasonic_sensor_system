"""The main script for logging the Arduino due output into data files. Running this script should
take care of: 1) logging the Arduino due output continuously, creating a new data file regularly,
2) saving the data files in compressed format in a folder based on date and time, 3) share relevant
data over UDP broadcasting. Any failure of this script (i.e., this script aborting or returning)
is a non recoverable failure of the logging; in this case, the full RPi and Mega should be restarted.
"""

# TODO: using some ugly way to set paths, i.e. with strings; move to a pathlib solution

import threading

import datetime
import os
import sys
import time

import arduino_logging

from utils import UDP_BROADCAST_PORT_NUMBER
from utils import MAIN_PATH_TO_DATA
from utils import MINUTES_INTERVAL
from utils import create_broadcastable_socket
from utils import get_broadcastable_interfaces
from utils import broadcast_on_interfaces
from utils import starttime_endtime
from utils import saving_filepath
from utils import dump_object

# ------------------------------------------------------------------------------------------
# make sure we are UTC
os.environ["TZ"] = "UTC"
time.tzset()

# ------------------------------------------------------------------------------------------
# the logging script itself

broadcastable_socket = create_broadcastable_socket()

print("logging start at time {}".format(datetime.datetime.now()))

# list of error times, to reboot if too many errors to close to each other
# i.e., we allow a few errors now and then and will recover from these (for example,
# some arduino packets alignment errors causing loss of data now and then), but if
# too many errors in a short time, we will abort the logging - which should be caught
# to perform a reboot.
list_error_times = []

# find the due port and make it ready to use
due_port_name = arduino_logging.find_due_serial()
print("script_logging.py starts with due on port: {}".format(due_port_name))
due_serial = arduino_logging.start_due_port(due_port_name)
print("script_logging.py is ready to use the Due")

# inform about that we start the logging
current_starttime, current_endtime = starttime_endtime(minutes_interval=MINUTES_INTERVAL)
print("script_logging.py at time {} setting current endtime and startime: {} - {}".format(datetime.datetime.now(), current_starttime, current_endtime))

# the list of packets to dump to file in the end
current_list_packets = []

# the list of interfaces on which to broadcast at present
list_broadcastable_interfaces = get_broadcastable_interfaces()

# the list of artemis 9-dof that we need to log
list_artemis_9dof_ports = arduino_logging.find_start_artemis_ports()

# need to avoid Due problem due to over full buffer: clean due buffer
while due_serial.inWaiting() > 0:
    due_serial.read()
arduino_logging.consume_semaphore(due_serial)

# also flush all the imus
for crrt_serial in list_artemis_9dof_ports:
    while crrt_serial.inWaiting() > 0:
        crrt_serial.read()

# perform logging forever; recover from lonely issues; crash on repeated issues,
# and expect that the caller will restart everything in this case.
while True:
    try:
        # as long as we are not after the expected data logfile, continue logging
        if datetime.datetime.now() < current_endtime:
            # log next packet
            packet_kind, decoded_packet = arduino_logging.get_one_packet(due_serial)
            # broadcast it on all interfaces
            udp_string = arduino_logging.format_packet_for_udp(packet_kind, decoded_packet)
            if udp_string is not None:
                broadcast_on_interfaces(broadcastable_socket, list_broadcastable_interfaces, udp_string, UDP_BROADCAST_PORT_NUMBER, raise_on_excep=False)
            udp_string = arduino_logging.format_packet_full_probes_for_udp(packet_kind, decoded_packet)
            if udp_string is not None:
                broadcast_on_interfaces(broadcastable_socket, list_broadcastable_interfaces, udp_string, UDP_BROADCAST_PORT_NUMBER, raise_on_excep=False)
            # save the packet in the list to save
            current_entry = (datetime.datetime.now(), packet_kind, decoded_packet)
            current_list_packets.append(current_entry)

        # otherwise, we are due for starting to log in a new file
        else:
            datetime_start_newdump = datetime.datetime.now()

            # dump the list ot save and touch a touchme file
            packets_to_dump = current_list_packets
            filepath = saving_filepath(current_starttime, current_endtime)
            touchfile = "{}/last_written.txt".format(MAIN_PATH_TO_DATA)
            print("script_logging.py perform threaded dump of current data chunk into file {}".format(filepath))

            # use another thread to dump data to avoid delays in the logging loop
            dump_thread = threading.Thread(target=dump_object, args=(filepath, packets_to_dump, touchfile))
            dump_thread.start()

            # prepare logging to a new file
            current_starttime, current_endtime = starttime_endtime(minutes_interval=MINUTES_INTERVAL)
            print("script_logging.py at time {} setting current endtime and startime: {} - {}".format(
                datetime.datetime.now(), current_starttime, current_endtime)
            )

            # reset list of packets and broadcastable interfaces for the next logging segment
            current_list_packets = []

            list_broadcastable_interfaces = get_broadcastable_interfaces()
            list_artemis_9dof_ports = arduino_logging.find_start_artemis_ports()

            # need to avoid Due problem due to over full buffer: clean due buffer
            # ugly: code repeat of higher up...
            while due_serial.inWaiting() > 0:
                due_serial.read()
            arduino_logging.consume_semaphore(due_serial)
            
            # also flush all the imus
            for crrt_serial in list_artemis_9dof_ports:
                while crrt_serial.inWaiting() > 0:
                    crrt_serial.read()

        # avoid using the full CPU time pulling the serial port; wait for a bit of data to have arrived before attemping to get a packer
        time_start_other_logging = datetime.datetime.now()
        # the reason for waiting for at least 5 bytes is that this way, if there are a few \n or \r here and there these will not interfer.
        while due_serial.inWaiting() < 5 and (datetime.datetime.now() - time_start_other_logging < datetime.timedelta(seconds=0.045)):
            # perform the logging of the artemis 9-dof, if there are some available
            list_packets_9dof = arduino_logging.log_9dof(list_artemis_9dof_ports)
            if list_packets_9dof is not None:
                for crrt_9dof_packet in list_packets_9dof:
                    crrt_to_broadcast = arduino_logging.format_packet_9dof_for_udp(crrt_9dof_packet)
                    broadcast_on_interfaces(broadcastable_socket, list_broadcastable_interfaces, crrt_to_broadcast, UDP_BROADCAST_PORT_NUMBER, raise_on_excep=False)
                    current_list_packets.append(crrt_9dof_packet)

            time.sleep(0.001)

    except Exception as e:
        # if we have an exception now and then it is not a big deal, just ignore; but if we get over 5 exceptions in the course of 5 seconds, it is time to
        # abort and restart from start, this is something bad happening
        print("script_logging.py received exception: {}".format(e))
        list_error_times.append(datetime.datetime.now())
        list_error_times = [crrt_datetime for crrt_datetime in list_error_times if crrt_datetime + datetime.timedelta(seconds=120.0) > datetime.datetime.now()]
        if len(list_error_times) > 120:
            print("script_logging.py received more than 120 errors in the last 120.0 seconds; abort")
            sys.exit(1)

