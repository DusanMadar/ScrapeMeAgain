#!/bin/sh

/bin/sh /scp/docker/entrypoint.base.sh

python3 /scp/scrapemeagain/distributed/ipstore/app.py &
# python3 /scp/scrapemeagain/distributed/controller/app.py &

# For dev only, to keep the container up.
tail -f /dev/null
