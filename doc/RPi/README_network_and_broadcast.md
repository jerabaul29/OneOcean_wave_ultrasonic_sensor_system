We got the network information from SL contacts:

- RPi gets static IP REDACTED.
- Range: REDACTED GW: n/a DNS: REDACTED DHCP range: REDACTED
- port REDACTED

## set static IP

### RPi side

```
cd /etc/
```

There edit ```dhcpcd.conf``` and add the content:

```
interface eth0
static ip_address=REDACTED
static domain_name_servers=REDACTED
```

### Computer side

If using a laptop or similar rather than the boat network for testing, need to set up the local network so that the static IPs are correct. For this:

- menu top right of Ubuntu
- Wired connection
- Wired settings
- add a new profile: RPi_static_ip
- set the relevant parameters:
  - IPv4 manual
  - Adresses: add REDACTED REDACTED REDACTED
  - DNS: REDACTED

## inspect traffic

To inspect traffic on a port from another computer on the network:

```
pi@raspberrypi:~ $ sudo tcpdump -X -i eth0 port REDACTED -v  # may need to update the port number and the interface
```
