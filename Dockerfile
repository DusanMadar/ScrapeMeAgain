FROM alpine:3.6

MAINTAINER "Dusan Madar"

COPY . /scp

WORKDIR /scp

RUN \
    apk --update add --no-cache \
        tor \
        privoxy \
        python3 \
        python3-dev \
        git \
        openssl && \
        wget -O /tmp/get-pip.py "https://bootstrap.pypa.io/get-pip.py" && \
        python3 /tmp/get-pip.py && \
        pip3 install -U pip && \
        pip3 install -r /scp/requirements.txt
