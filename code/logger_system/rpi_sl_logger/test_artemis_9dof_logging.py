import arduino_logging

res = arduino_logging.find_start_artemis_ports()

while True:
    list_packets = arduino_logging.log_9dof(res)
    if list_packets is not None:
        print(list_packets)
        print(arduino_logging.format_packet_9dof_for_udp(list_packets[0]))

