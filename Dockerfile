FROM alpine:3.6

ENV TOR_PORT=9051
ENV TOR_PASSWORD="I-solemnly-swear-I-am-up-to-no-good"

MAINTAINER "Dusan Madar"

# Runtime dependencies.
RUN \
    apk --update add --no-cache \
        tor \
        privoxy \
        python3 \
        python3-dev \
        curl \
        git \
        openssl && \
        wget -O /tmp/get-pip.py "https://bootstrap.pypa.io/get-pip.py" && \
        python3 /tmp/get-pip.py && \
        pip3 install -U pip

# Configuration.
RUN \
    echo 'RunAsDaemon 1' >> /etc/tor/torrc && \
    echo "ControlPort $TOR_PORT" >> /etc/tor/torrc && \
    echo $(echo "HashedControlPassword") $(tor --hash-password $TOR_PASSWORD | tail -n 1) >> /etc/tor/torrc && \
    echo "forward-socks5t / 127.0.0.1:9050 ." >> /etc/privoxy/config

# Scraper files and dependencies.
COPY . /scp
RUN pip3 install -r /scp/requirements.txt

CMD privoxy /etc/privoxy/config; tor
