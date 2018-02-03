#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Configure and run Privoxy.
> /etc/privoxy/config   # Clear the file to avoid duplicate lines.
echo "listen-address $PRIVOXY_HOST:$PRIVOXY_PORT" >> /etc/privoxy/config
echo "forward-socks5t / $PRIVOXY_HOST:9050 ." >> /etc/privoxy/config
privoxy /etc/privoxy/config

# Configure and run Tor.
> /etc/tor/torrc        # Clear the file to avoid duplicate lines.
echo 'RunAsDaemon 1' >> /etc/tor/torrc
echo "ControlPort $TOR_PORT" >> /etc/tor/torrc
echo $(echo "HashedControlPassword") $(tor --hash-password $TOR_PASSWORD | tail -n 1) >> /etc/tor/torrc
tor
