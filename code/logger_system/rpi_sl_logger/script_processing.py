from utils import datetime_next_newfile
from utils import starttime_endtime
from utils import create_broadcastable_socket
from utils import get_broadcastable_interfaces
from utils import broadcast_on_interfaces
from utils import saving_filepath
from utils import processing_filepath

from utils import UDP_BROADCAST_PORT_NUMBER
from utils import MINUTES_INTERVAL

from wave_processing import compute_wave_elevation
from wave_processing import compute_SWH
from wave_processing import load_data_dump
from wave_processing import INSTALLATION_PROPERTIES
from wave_processing import format_swh_4sigma_for_udp

import os
import time

import datetime

# ------------------------------------------------------------------------------------------
# make sure we are UTC
os.environ["TZ"] = "UTC"
time.tzset()

# ------------------------------------------------------------------------------------------
# UDP socket for broadcasting readings
broadcastable_socket = create_broadcastable_socket()

# ------------------------------------------------------------------------------------------
# perform the analysis when it is needed

# taking a few extra sleep seconds after a segment should be dumped, to let time for files to be written etc
# 120 is way overkill, but fine enough
EXTRA_SLEEP_SECONDS = 120

while True:
    try:
        # ----------------------------------------
        # when should the next file to process be ready?

        current_datetime = datetime.datetime.utcnow()
        crrt_datetime_next_newfile = datetime_next_newfile(current_datetime)
        current_starttime, current_endtime = starttime_endtime(minutes_interval=MINUTES_INTERVAL, current_time=current_datetime)

        seconds_to_datetime_next_newfile = (crrt_datetime_next_newfile - datetime.datetime.utcnow()).total_seconds() + EXTRA_SLEEP_SECONDS
        print("next newfile is at UTC {}; sleep for {} seconds".format(crrt_datetime_next_newfile, seconds_to_datetime_next_newfile))

        filepath = saving_filepath(current_starttime, current_endtime)
        print("file to read in will be: {}".format(filepath))

        time.sleep(seconds_to_datetime_next_newfile + 120)

        # ----------------------------------------
        # perform processing

        dict_data = load_data_dump(filepath, show_interpolation=False)
        crrt_probe = "gauge_ug1_meters"
        dict_data = compute_wave_elevation(dict_data, INSTALLATION_PROPERTIES, probe=crrt_probe, plot=False)

        # compute the wave properties: SWH
        # for now, only use 4 * std(eta)
        SWH_4std = compute_SWH(dict_data["list_time_series_interpolated"]["water_elevation_{}".format(crrt_probe)])

        print("computed SWH: {}".format(SWH_4std))

        # ----------------------------------------
        # make sure to attempt to use the latest networks available
        list_broadcastable_interfaces = get_broadcastable_interfaces()
        time.sleep(10)

        # ----------------------------------------
        # share the SWH on the network

        udp_string = format_swh_4sigma_for_udp(SWH_4std)
        print("broadcast: {}".format(udp_string))

        if udp_string is not None:
            broadcast_on_interfaces(broadcastable_socket, list_broadcastable_interfaces, udp_string, UDP_BROADCAST_PORT_NUMBER, raise_on_excep=False)

        # ----------------------------------------
        # dump the results in an analysis file

        filepath_results = processing_filepath(current_starttime, current_endtime)

        with open(filepath_results, "w") as fh:
            fh.write(udp_string.decode())
            fh.write("\n")

    except Exception as e:
        print("script_processing.py received exception: {}".format(e))

