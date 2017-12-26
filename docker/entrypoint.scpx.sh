#!/bin/sh

/bin/sh /scp/docker/entrypoint.base.sh

# For dev only, to keep the container up.
tail -f /dev/null
