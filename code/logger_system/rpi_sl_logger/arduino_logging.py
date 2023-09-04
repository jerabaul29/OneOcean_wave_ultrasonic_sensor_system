"""A set of simple helper functions that allow to fully log the gauges arduino output.
This allows in particular to easily: 1) find the arduino due logger, 2) grab packets
for the gauges or the IMU from the arduino due logger, as well as semaphores if gets
out of alignment, 3) convert the ADC readings into actual distance measurements 4) format
data for sharing on UDP broadcasting network.
"""

# TODO: add a CRC on gague data packet, from both the Arduino side (put CRC) and the decoding side (check validity)? Add to the GaugesPacket structure?
# NOTE: we expect that the UG probes are on channels 1 and 2, and that the radar probe is on channel 3, of the gauge packets (the actual ADC
# channels on the Arduino may differ of course).

import numpy as np

import sys

from crcmod import mkCrcFun

import time
import os

import datetime

import struct
import binascii

from dataclasses import dataclass

import serial
import serial.tools.list_ports

# ------------------------------------------------------------------------------------------
# make sure we are UTC
os.environ["TZ"] = "UTC"
time.tzset()


@dataclass
class GaugesPacket:
    reading_time: int     # arduino clock reading time (milliseconds)
    reading_number: int   # arduino reading number (ie number of times all ADC channels have been read)
    value_1: int
    value_2: int
    value_3: int


@dataclass
class VN100Packet:
    # The VN100 header looks like:
    # MagX, MagY, MagZ, AccX, AccY, AccZ, GyroX, GyroY, GyroZ, Temp, Pres, Yaw, Pitch, Roll, DCM1,
    # DCM2, DCM3, DCM4, DCM5, DCM6, DCM7, DCM8, DCM9, MagNED1, MagNED2, MagNED3, AccNED1, AccNED2, ACCNED3
    # keeping only a few interesting parameters in actual final data packages
    reading_time: int      # the reading time, arduino clock (milliseconds)
    reading_number: int    # the reading number, arduino count, i.e. number of the VN100 packet
    acc_x: float
    acc_y: float
    acc_z: float
    yaw: float
    pitch: float
    roll: float
    acc_N: float
    acc_E: float
    acc_D: float
    crc: bool               # the CRC validity of the binary packet


@dataclass
class Artemis9dofIMUPacket:
    millis_timestamp: int
    acc_N: float
    acc_E: float
    acc_D: float
    yaw__: float
    pitch: float
    roll_: float
    metadata: int


class StreamMatcher(object):
    """Given a stream of bytes available on by one, return true each
    time the last bytes are matching a given pattern."""
    def __init__(self, binary_string_to_match):
        self.to_match = binary_string_to_match
        self.length_to_match = len(self.to_match)
        self.current_number_matched = 0

    def match(self, binary_char_to_match):
        char_in = int.from_bytes(binary_char_to_match, byteorder=sys.byteorder)
        if self.to_match[self.current_number_matched] == char_in:
            self.current_number_matched += 1

            if self.current_number_matched == self.length_to_match:
                self.current_number_matched = 0
                return True
        else:
            self.current_number_matched = 0
            return False


def consume_semaphore(due_serial):
    """Consume a semaphore; this can be use to re-align data."""
    semaphore_matcher = StreamMatcher(b"S SEMAPHORE\r\n")
    while True:
        if due_serial.inWaiting() > 0:
            crrt_char = due_serial.read()
            if semaphore_matcher.match(crrt_char):
                return


def find_due_serial():
    """Find the port to the Arduino Due; we expect only 1 arduino
    Due to be connected, i.e., once it is found, it is the correct
    one."""
    ports = serial.tools.list_ports.comports()

    for crrt_port in ports:
        port_name = crrt_port.name
        port_product = crrt_port.product

        if port_product == "Arduino Due Prog. Port":
            return "/dev/{}".format(port_name)

    raise RuntimeError("Could not find any Arduino Due!")

    return None


def find_start_artemis_ports():
    """Find the ports on which we have artemis 9dof based IMUs.
    """

    # first check for correct kind of port product, though not very discriminative...
    list_possible_artemis_9dof_ports = []

    ports = serial.tools.list_ports.comports()

    for crrt_port in ports:
        port_name = crrt_port.name
        port_product = crrt_port.product

        if port_product == "USB Serial":
            crrt_port = "/dev/{}".format(port_name)
            list_possible_artemis_9dof_ports.append(crrt_port)

    # then, look for the correct semaphore: is this actually the port we need?
    list_artemis_serials = []

    for crrt_port in list_possible_artemis_9dof_ports:
        crrt_serial = serial.Serial(crrt_port, baudrate=57600)
        crrt_serial.flushInput()
        crrt_serial.flushOutput()
        time.sleep(20.0)  # after a reboot, the artemis imu needs time to heat up...

        # read the content
        list_chars = []
        while crrt_serial.inWaiting() > 0:
            list_chars.append(crrt_serial.read())

        # can we find a semaphore?
        semaphore_matcher = StreamMatcher(b"SEMAPHORE_EXTRA_IMU\r\n")
        for crrt_char in list_chars:
            if semaphore_matcher.match(crrt_char):
                print("found artemis 9dof imu on serial: {}".format(crrt_serial))
                list_artemis_serials.append(crrt_serial)
                break

    return list_artemis_serials


def log_individual_9dof(ser):
    """Log one available message for the given 9dof if available, else
    return None."""
    
    # make sure that ready to read a message
    if ser.inWaiting() > 5:
        # consume the semaphore
        semaphore = StreamMatcher(b"SEMAPHORE_EXTRA_IMU\r\n")
        got_semaphore = False
        time_start_wait_for_semaphore = datetime.datetime.now()
        while True and (datetime.datetime.now() - time_start_wait_for_semaphore < datetime.timedelta(seconds=0.01)):
            if ser.inWaiting() > 0:
                crrt_char = ser.read()
                if semaphore.match(crrt_char):
                    got_semaphore = True
                    break

        if not got_semaphore:
            return None

        # consume the packet of data
        SIZEOF_9DOF_PACKET = 32
        list_bytes = []
        crrt_byte_number = 0

        got_message = False
        time_start_wait_for_message = datetime.datetime.now()
        while True and (datetime.datetime.now() - time_start_wait_for_message < datetime.timedelta(seconds=0.01)):
            if ser.inWaiting() > 0:
                crrt_byte = ser.read()
                list_bytes.append(crrt_byte)
                crrt_byte_number += 1
                if crrt_byte_number == SIZEOF_9DOF_PACKET:
                    got_message = True
                    break
        if not got_message:
            return None

        # unpack
        packed_struct = b"".join(list_bytes)
        unpacked_9dof_packet = struct.unpack("IffffffI", packed_struct)

        packet = Artemis9dofIMUPacket(
            millis_timestamp=unpacked_9dof_packet[0],
            acc_N=unpacked_9dof_packet[1],
            acc_E=unpacked_9dof_packet[2],
            acc_D=unpacked_9dof_packet[3],
            yaw__=unpacked_9dof_packet[4],
            pitch=unpacked_9dof_packet[5],
            roll_=unpacked_9dof_packet[6],
            metadata=unpacked_9dof_packet[7],
        )

        # TODO: check that the 2 next chars are the end of the message; if not, return kind None
        # and flush the buffer

        return (datetime.datetime.now(), "9dof", packet)

    # if not, just return None
    else:
        return None


def log_9dof(list_9dof_ports):
    """For each of the ports in the list_9dof_ports, log all full available messages."""

    list_packets_9dof = []

    for crrt_port in list_9dof_ports:
        datetime_start = datetime.datetime.now()
        while True and (datetime.datetime.now() - datetime_start < datetime.timedelta(seconds=0.015)):
            crrt_result = log_individual_9dof(crrt_port)
            if crrt_result is None:
                break
            else:
                list_packets_9dof.append(crrt_result)

    if len(list_packets_9dof) == 0:
        return None
    else:
        return list_packets_9dof


def start_due_port(port_name, baudrate=115200, perform_restart=True):
    """Given the port name on which the Due is connected, start
    the port with the correct parameters. Ask for a restart of
    the board and start again from a "clean" state."""

    print("start due port")
    due_serial = serial.Serial(port_name, baudrate)

    if perform_restart:
        print("perform full due restart")
        # restart and check for correct boot message
        due_serial.write("BOOT".encode("ASCII"))
        time.sleep(750.0 / 1000.0)
        due_serial.flushInput()
        due_serial.flushOutput()
        while due_serial.inWaiting() > 0:
            due_serial.read()

        list_chars = []
        while True:
            if due_serial.inWaiting() > 0:
                list_chars.append(due_serial.read().decode())

                if list_chars[-1] == "\n":
                    message = "".join(list_chars)
                    break

        if (message[:-2] == "S BOOT_ARD_DUE_SL_LOGGER"):
            return due_serial
        else:
            raise RuntimeError("Wrong Arduino Due startup message: {}".format(message[:-1]))

        return None

    else:
        print("no due restart, find semaphore")
        consume_semaphore(due_serial)
        return due_serial


def consume_end_of_packet(due_serial):
    """Consume the end of packet, i.e. the E\n termination sequence. If
    such end of packet is not obtained as expected, raise a RuntimeError."""
    list_bytes = []
    crrt_byte_number = 0
    while True:
        if due_serial.inWaiting() > 0:
            crrt_byte = due_serial.read()
            crrt_byte_number += 1
            list_bytes.append(crrt_byte)
            if crrt_byte_number == 2:
                break

    if not (list_bytes[0] == b"E" and list_bytes[1] == b"\n"):
        raise RuntimeError("wrong end of packet; got {}".format(list_bytes))


def get_one_G_packet(due_serial):
    """Given that a G packet is being received, i.e. that a G byte has been
    received, grab the full packet until its end and return it."""

    SIZE_G_struct = 20

    list_bytes = []
    crrt_byte_number = 0

    # read the whole struct
    while True:
        if due_serial.inWaiting() > 0:
            crrt_byte = due_serial.read()
            list_bytes.append(crrt_byte)
            crrt_byte_number += 1
            if crrt_byte_number == SIZE_G_struct:
                break

    # unpack
    packed_struct = b"".join(list_bytes)
    unpacked_G_packet = struct.unpack("IIiii", packed_struct)

    # check that we get the end of packet marker
    consume_end_of_packet(due_serial)

    packet = GaugesPacket(
        unpacked_G_packet[0],
        unpacked_G_packet[1],
        unpacked_G_packet[2],
        unpacked_G_packet[3],
        unpacked_G_packet[4]
    )

    return packet


def get_one_I_packet(due_serial):
    """Given that an I packet is being received, i.e. that a I bye has been
    received, grab the full packet until its end and return it."""

    # the total size of the struct being transmitted over USB
    SIZE_I_STRUCT_BYTES = 132

    # size of the metadata
    SIZE_METADATA_BYTES = 8
    # size of one binary dataframe
    SIZE_FRAME_BYTES = 124

    assert SIZE_METADATA_BYTES + SIZE_FRAME_BYTES == SIZE_I_STRUCT_BYTES

    # number of 4 bits floating points in one frame
    NUMBER_VN100_FIELDS = 29
    # size of the actual data
    SIZE_DATA_BYTES = 4 * NUMBER_VN100_FIELDS
    # size of the CRC
    SIZE_CRC_BYTES = 2
    # size of the header; will be at the end of the packet due to how it is being logged
    SIZE_HEADER_BYTES = 6

    assert SIZE_FRAME_BYTES == SIZE_DATA_BYTES + SIZE_CRC_BYTES + SIZE_HEADER_BYTES

    # the binary header
    BINARY_HEADER = b"\xfa\x14\x3e\x00\x3a\x00"

    # the crc decode
    crc16 = mkCrcFun(0x11021, 0x0000, False, 0x0000)

    list_bytes = []
    crrt_byte_number = 0

    # read the whole struct
    while True:
        if due_serial.inWaiting() > 0:
            crrt_byte = due_serial.read()
            list_bytes.append(crrt_byte)
            crrt_byte_number += 1
            if crrt_byte_number == SIZE_I_STRUCT_BYTES:
                break

    packed_struct = b"".join(list_bytes)
    assert len(packed_struct) == SIZE_I_STRUCT_BYTES, "got wrong IMU struct size"

    # extract the different parts of the struct
    metadata_part = packed_struct[0:SIZE_METADATA_BYTES]
    data_part = packed_struct[SIZE_METADATA_BYTES:SIZE_METADATA_BYTES+SIZE_DATA_BYTES]
    crc_part = packed_struct[SIZE_METADATA_BYTES+SIZE_DATA_BYTES:SIZE_METADATA_BYTES+SIZE_DATA_BYTES+SIZE_CRC_BYTES]
    header_last_part = packed_struct[SIZE_METADATA_BYTES+SIZE_DATA_BYTES+SIZE_CRC_BYTES:]

    # check that we got the header right
    assert BINARY_HEADER == header_last_part

    # check that we get the end of packet marker
    consume_end_of_packet(due_serial)

    # unpack the metadata
    unpacked_I_metadata = struct.unpack("II", metadata_part)

    # unpack the actual data
    unpacked_I_packet = struct.unpack(NUMBER_VN100_FIELDS*'f', data_part)

    # check CRC
    crc1 = np.int('0x' + binascii.hexlify(crc_part).decode("ASCII"), 16)
    crc2 = crc16(BINARY_HEADER[1:] + data_part)
    valid_flag = (crc1 == crc2)

    if not valid_flag:
        print("WARNING; invalid crc on IMU packet: {}".format(packed_struct))

    packet = VN100Packet(
        unpacked_I_metadata[0],
        unpacked_I_metadata[1],
        unpacked_I_packet[3],
        unpacked_I_packet[4],
        unpacked_I_packet[5],
        unpacked_I_packet[11],
        unpacked_I_packet[12],
        unpacked_I_packet[13],
        unpacked_I_packet[26],
        unpacked_I_packet[27],
        unpacked_I_packet[28],
        valid_flag
    )

    return packet


def get_one_packet(due_serial):
    """Get the next packet of data from the Arduino Due, and return a fully
    decoded and ready to use packet."""
    while True:
        if due_serial.inWaiting() > 0:
            char_packet_kind = due_serial.read().decode()
            break
        else:
            time.sleep(0.005)

    if char_packet_kind == "G":
        decoded_packet = get_one_G_packet(due_serial)
    elif char_packet_kind == "I":
        decoded_packet = get_one_I_packet(due_serial)
    elif char_packet_kind in ["D", "W", "S"]:
        decoded_packet = [char_packet_kind]
        while True:
            if due_serial.inWaiting() > 0:
                crrt_char = due_serial.read().decode("ASCII")
                decoded_packet.append(crrt_char)
                if crrt_char == "\n":
                    decoded_packet = "".join(decoded_packet[:-1])
                    break
    else:
        print("WARNING unknown packet kind: {}".format(char_packet_kind))
        print("find next semaphore to re-align data grabbing")
        consume_semaphore(due_serial)

    return char_packet_kind, decoded_packet


def reading_to_amps(reading, Rohm, n_bits_adc=12, v_max=3.3):
    """To be used together with current loop measurements.
    Given an ADC reading (i.e. reading) with number of bits n_bits_adc and
    corresponding max voltage v_max, and given that this is the reading of
    the voltage induced by a current loop onto a resistor of value Rohm,
    return the actual current in Amps of the current loop."""
    Uv = reading / (2**n_bits_adc - 1) * v_max
    Ia = Uv / Rohm
    return Ia


def convert_g_packet_adc_to_distances(g_packet, R1ohm=160.0, R2ohm=160.0, R3ohm=160.0, n_bits_adc=12, v_max=3.3):
    """Given a gauges packet (g_packet), and the value of the resistors on the loops corresponding to
    gauge 1 (R1ohm), 2 (R2ohm), and 3 (R3ohm), and the ADC properties (n_bits_adc and v_max),
    get the corresponding reading. In our case, this is actually being wired to 2 UGs (values 1 and 2),
    and to 1 radar probe (value 3). The conversion factors are for the specific probes we use, see comments
    around the conversions."""
    adc_1 = g_packet.value_1  # UG1
    adc_2 = g_packet.value_2  # UG2
    adc_3 = g_packet.value_3  # radar

    # the UGs are 0.4 to 15.2m, for 4 to 20mA; see the IRU-3430 datasheet

    value_1 = 0.4 + (reading_to_amps(adc_1, R1ohm) - 0.004) * (15.2 - 0.4) / (0.020 - 0.004)
    value_2 = 0.4 + (reading_to_amps(adc_2, R2ohm) - 0.004) * (15.2 - 0.4) / (0.020 - 0.004)

    # the radar is 0.3 to 15m, for 4 to 20mA; see the PRL-050 datasheet

    value_3 = 0.3 + (reading_to_amps(adc_3, R3ohm) - 0.004) * (15.0 - 0.3) / (0.020 - 0.004)

    return (value_1, value_2, value_3)


def compute_checksum(nmea_msg):
    # TODO: rename to compute_NMEA_checksum
    """Compute NMEA 0183 checksum on a string. Skips leading ! or $ and stops
    at *.
    """

    # Find the start of the NMEA sentence
    start_chars = ["!", "$"]
    ind_start = None
    for ind, crrt_char in enumerate(nmea_msg):
        if crrt_char in start_chars:
            ind_start = ind + 1
            break

    # Find the end of the NMEA sentence
    ind_stop = None
    for ind, crrt_char in enumerate(nmea_msg):
        if crrt_char == "*":
            ind_stop = ind
            break

    # default values for start and stop inds if no hard delimiters
    if ind_start is None:
        ind_start = 0

    if ind_stop is None:
        ind_stop = len(nmea_msg)

    # Calculate the checksum on the message
    checksum = 0
    for crrt_char in nmea_msg[ind_start:ind_stop]:
        checksum = checksum ^ ord(crrt_char)
    checksum = checksum & 0xFF

    # convert checksum to hex representation
    checksum_hex = hex(checksum)[-2:]
    checksum_hex = checksum_hex.upper()

    return checksum_hex


def format_packet_full_probes_for_udp(packet_kind, decoded_packet):
    str_packet = None

    if packet_kind == "G":
        distance_1, distance_2, distance_3 = convert_g_packet_adc_to_distances(decoded_packet)

        str_packet = "$PROBES_WS_ALL,{:06.3f},{:06.3f},{:06.3f}".format(distance_1, distance_2, distance_3)

    if str_packet is not None:
        checksum = compute_checksum(str_packet)
        str_packet += "*{}".format(checksum)
        str_packet += "\r\n"
        str_packet = str_packet.encode("ascii")

    return str_packet


def format_packet_9dof_for_udp(decoded_packet):
    decoded_packet = decoded_packet[2]
    str_packet = "$EXTRA_IMU_9DOF,{:+07.2f},{:+07.2f},{:+08.4f},{:04}".format(
        decoded_packet.pitch,
        decoded_packet.roll_,
        decoded_packet.acc_D,
        decoded_packet.metadata
    )

    if str_packet is not None:
        checksum = compute_checksum(str_packet)
        str_packet += "*{}".format(checksum)
        str_packet += "\r\n"
        str_packet = str_packet.encode("ascii")

    return str_packet


def format_packet_for_udp(packet_kind, decoded_packet):
    """Given a packet kind and packet, return a plaintext string
    in NMEA format to be shared on UDP. For packets that do not need
    to be shared on UDP, such as semaphore packets, just return
    None and the caller will know that there is nothing to broadcast."""

    if packet_kind == "G":
        distance_1, distance_2, distance_3 = convert_g_packet_adc_to_distances(decoded_packet)

        str_packet = "$PROBES_WS,{:06.3f}".format(distance_1)

    elif packet_kind == "I":
        pitch = decoded_packet.pitch
        roll = decoded_packet.roll
        acc_X = decoded_packet.acc_x
        acc_Y = decoded_packet.acc_y
        acc_Z = decoded_packet.acc_z
        acc_D = decoded_packet.acc_D

        str_packet = "$IMU_VN100_WS,{:+07.2f},{:+07.2f},{:+07.2f},{:+08.4f},{:+08.4f},{:+08.4f}".format(
            pitch,
            roll,
            acc_X,
            acc_Y,
            acc_Z,
            acc_D
        )

    else:
        str_packet = None

    if str_packet is not None:
        checksum = compute_checksum(str_packet)
        str_packet += "*{}".format(checksum)
        str_packet += "\r\n"
        str_packet = str_packet.encode("ascii")

    return str_packet


# ------------------------------------------------------------------------------------------
# simple script for grabbing

if __name__ == "__main__":
    due_port_name = find_due_serial()
    print("Found Arduino due on port {}".format(due_port_name))
    due_serial = start_due_port(due_port_name)
    print("Arduino ready to use")

    while True:
        packet_kind, decoded_packet = get_one_packet(due_serial)
        print(decoded_packet)

