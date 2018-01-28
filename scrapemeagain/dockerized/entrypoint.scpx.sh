#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Wait till the master scraper is up and running.
python3 /scp/scrapemeagain/dockerized/healthcheck/test.py $HEALTHCHECK_HOST $HEALTHCHECK_PORT
/bin/sh /scp/scrapemeagain/dockerized/entrypoint.base.sh

python3 -u /scp/scrapemeagain/scrapers/$SCRAPER_PACKAGE/main_dockerized.py

# For dev only, to keep the container up.
# tail -f /dev/null
