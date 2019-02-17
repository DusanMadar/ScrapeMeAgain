FROM alpine:3.6

MAINTAINER "Dušan Maďar"

ENV SCP_DIR=/scp
ENV APP_DIR=/scrapemeagain
ENV APP_SRC_DIR=$APP_DIR$APP_DIR
ENV PYTHONPATH="${PYTHONPATH}:${SCP_DIR}:${APP_DIR}"

RUN \
    mkdir -p $SCP_DIR $APP_SRC_DIR && \
    apk --update add --no-cache \
        tor \
        privoxy \
        python3 \
        libressl

COPY requirements.txt $APP_DIR/requirements.txt

RUN \
    wget -O /tmp/get-pip.py "https://bootstrap.pypa.io/get-pip.py" && \
    python3 /tmp/get-pip.py && \
    pip3 install --no-cache-dir -U pip && \
    pip3 install --no-cache-dir -r $APP_DIR/requirements.txt

COPY scrapemeagain $APP_SRC_DIR
COPY tests $APP_DIR/tests

# The line belows adds postgres support and another 120 mb to the image size.
# RUN apk add --update --no-cache gcc musl-dev postgresql-dev
