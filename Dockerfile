FROM alpine:latest

ENV TOR_PORT=9051
ENV TOR_PASSWORD="I solemnly swear I am up to no good"

RUN apk --update add tor privoxy && \
    echo 'RunAsDaemon 1' >> /etc/tor/torrc && \
    echo "ControlPort $TOR_PORT" >> /etc/tor/torrc && \
    echo "HashedControlPassword $(tor --hash-password TOR_PASSWORD | tail -n 1)"  >> /etc/tor/torrc && \
    echo "forward-socks5t / 127.0.0.1:9050 ." >> /etc/privoxy/config
