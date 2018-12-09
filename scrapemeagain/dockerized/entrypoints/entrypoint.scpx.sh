#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Wait till the master scraper is up and running.
python3 $APP_SRC_DIR/dockerized/apps/healthcheck/test.py $HEALTHCHECK_HOST $HEALTHCHECK_PORT
/bin/sh $APP_SRC_DIR/dockerized/entrypoints/entrypoint.base.sh

python3 -u $SCP_DIR/$SCRAPER_PACKAGE/main_dockerized.py

# For dev only, to keep the container up.
# tail -f /dev/null
