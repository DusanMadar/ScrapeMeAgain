#!/bin/sh

/bin/sh /scp/docker/entrypoint.base.sh

# Wait for each sub-service to start before starting anotherone.
python3 /scp/scrapemeagain/dockerized/ipstore/app.py &
python3 /scp/scrapemeagain/dockerized/healthcheck/test.py $IPSTORE_HOST $IPSTORE_PORT
python3 /scp/scrapemeagain/dockerized/urlbroker/app.py &
python3 /scp/scrapemeagain/dockerized/healthcheck/test.py $URLBROKER_HOST $URLBROKER_PORT
python3 /scp/scrapemeagain/dockerized/healthcheck/app.py &
python3 /scp/scrapemeagain/dockerized/healthcheck/test.py $HEALTHCHECK_HOST $HEALTHCHECK_PORT

python3 /scp/scrapemeagain/scrapers/$SCRAPER_PACKAGE/main_dockerized.py

python3 -c 'from scrapemeagain.dockerized.utils import wait_for_other_scrapers; wait_for_other_scrapers()'

# For dev only, to keep the container up.
# tail -f /dev/null
