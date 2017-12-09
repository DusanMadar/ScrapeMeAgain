#!/bin/sh

# Configure and run Privoxy.
> /etc/privoxy/config   # Clear the file to avoid duplicate lines.
echo "forward-socks5t / 127.0.0.1:9050 ." >> /etc/privoxy/config
privoxy /etc/privoxy/config

# Configure and run Tor.
> /etc/tor/torrc        # Clear the file to avoid duplicate lines.
echo 'RunAsDaemon 1' >> /etc/tor/torrc
echo "ControlPort $TOR_PORT" >> /etc/tor/torrc
echo $(echo "HashedControlPassword") $(tor --hash-password $TOR_PASSWORD | tail -n 1) >> /etc/tor/torrc
tor
