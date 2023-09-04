import datetime
import os
import time

import compress_pickle as cpkl

import math

import socket
import netifaces as ni

# ------------------------------------------------------------------------------------------
# make sure we are UTC
os.environ["TZ"] = "UTC"
time.tzset()

# ------------------------------------------------------------------------------------------
# a few helpers about the network


def get_broadcastable_interfaces():
    """Return a list of the broadcastable interfaces; each entry of the list is a tuple
    (interface, broadcast ip)."""

    # find the available interfaces
    list_interfaces = os.listdir('/sys/class/net/')
    # we do not need to broadcast to lo
    list_interfaces.remove('lo')

    # we need a list of the (interfaces, broadcast) for the interfaces that support broadcast
    list_interface_ipbroadcast = []

    for crrt_interface in list_interfaces:
        # not all interfaces can perform broadcast; we expect that on the boat only IPv4 interfaces
        # are found, but never know, be careful (for example, IPv6 interfaces do not allow broadcast;
        # multicast should be used on these instead).
        try:
            crrt_properties = ni.ifaddresses(crrt_interface)[ni.AF_INET][0]
            if "broadcast" in crrt_properties.keys():
                crrt_entry = (crrt_interface, crrt_properties["broadcast"])
                list_interface_ipbroadcast.append(crrt_entry)
        except Exception as e:
            print("could not perform broadcast on interface {}, got exception {}".format(crrt_interface, e))

    return list_interface_ipbroadcast


def create_broadcastable_socket():
    """Create a socket that can be used to broadcast data."""
    # create the actual socket to use
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    return udp_socket


def broadcast_on_interfaces(broadcastable_socket, list_broadcastable_interfaces, to_broadcast, UDP_port_number, raise_on_excep=False):
    """Broadcast to_broadcast on list_broadcastable_interfaces, which is the output from
    get_broadcastable_interfaces, using broadcastable_socket, which is the output of
    create_broadcastable_socket. If raise_on_excep is True, then hitting errors raise an
    except. This can be de-activated to make things more robust to for example network
    interruptions."""

    for (crrt_interface, crrt_ip) in list_broadcastable_interfaces:
        try:
            broadcastable_socket.sendto(to_broadcast, (crrt_ip, UDP_port_number))
        except Exception as e:
            if raise_on_excep:
                raise e
            else:
                # print("ignore excep {} when attempting to broadcast".format(e))
                pass

# ------------------------------------------------------------------------------------------
# a few helper functions related to the datetimes of start and end of data logfiles and paths


def datetime_next_newfile(datetime_in, minutes_interval=30):
    """Given the datetime_in provided, and the interval duration of logging, find the datetime
    when the next data file should be created. This datetime is chosen so that the minutes of the
    start of the next data logfile is a multiple of minutes_interval. For example, for minutes_interval=30,
    a new data logfile should be started at time HH:00 and time HH:30."""
    datetime_upper_bound = datetime_in + datetime.timedelta(minutes=minutes_interval + 1.0)  # use 1 extra minute to avoid exact 60, just in case...
    crrt_datetime_next_newfile = datetime.datetime(
        year   = datetime_upper_bound.year,
        month  = datetime_upper_bound.month,
        day    = datetime_upper_bound.day,
        hour   = datetime_upper_bound.hour,
        minute = minutes_interval * math.floor(datetime_upper_bound.minute / minutes_interval),
        second = 0
    )
    return crrt_datetime_next_newfile


def starttime_endtime(minutes_interval=30, current_time=None):
    """Generate datetimes corresponding to the current start and end time for time segments
    of length minutes_interval. For example, if time is HH:12, the startime and endtime will be
    HH:00 and HH:30."""
    current_time = datetime.datetime.now()
    current_starttime = datetime.datetime(
        year   = current_time.year,
        month  = current_time.month,
        day    = current_time.day,
        hour   = current_time.hour,
        minute = minutes_interval * math.floor(current_time.minute / minutes_interval),
        second = 0
    )
    current_endtime = current_starttime + datetime.timedelta(minutes=minutes_interval)

    return current_starttime, current_endtime


def dump_object(filepath, to_dump, touchfile=None):
    """A minor helper to dump the to_dump object into filepath. filepath
    is the path where the object should be dumped including the path and
    filepath, to_dump is the object to dump there, and touchfile is the path
    and filepath to the file to touch to indicate that this method was performed.
    If touchfile is None, no touching takes place.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "bw") as fh:
        cpkl.dump(to_dump, fh, compression="lzma", set_default_extension=False)
    if touchfile is not None:
        with open(touchfile, "w") as fh:
            fh.write("{}".format(datetime.datetime.now()))


def saving_middlepath(datetime_start):
    """The saving middlepath corresponding to datetime_start. This is
    a YYYY/MM/DD/ path string, so that we can save files inside daily
    data folders with fixed format."""
    string_middlename_location = "{:04}/{:02}/{:02}/".format(datetime_start.year, datetime_start.month, datetime_start.day)
    return string_middlename_location


def saving_filepath(starttime, endtime):
    """Given the starttime and endtime of a logging interval / dump, return the full relative
    path to the data file."""
    middlename_location = saving_middlepath(starttime)
    filepath = "{}/{}/{}__{}.pkl.lzma".format(MAIN_PATH_TO_DATA, middlename_location, starttime, endtime)
    filepath = filepath.replace(" ", "_")

    return filepath


def processing_filepath(starttime, endtime):
    """Give the current starttime and endtime, return the full relative path to the processing output
    file."""
    middlename_location = saving_middlepath(starttime)
    filepath = "{}/{}/{}__{}_results.txt".format(MAIN_PATH_TO_DATA, middlename_location, starttime, endtime)
    filepath = filepath.replace(" ", "_")

    return filepath


# ------------------------------------------------------------------------------------------
# TODO: move to params

# which port we broadcast on
UDP_BROADCAST_PORT_NUMBER = REDACTED

# where we store the data: locally, in data folder
MAIN_PATH_TO_DATA = "../../../data"

# how often to write to a new file, perform analysis, etc
MINUTES_INTERVAL = 30
