#!/bin/sh

# NOTE any `python3` process accessing `config.Config` needs to call
# `apply_scraper_config()` in order to use current scraper's config!

# Exit immediately if a command exits with a non-zero status.
set -e

/bin/sh /scp/scrapemeagain/dockerized/entrypoints/entrypoint.base.sh

# Ensure `useragents.json` is ready.
python3 -c 'from scrapemeagain.utils.useragents import get_user_agents; get_user_agents()'

# Wait for each sub-service to start before starting anotherone.
python3 /scp/scrapemeagain/dockerized/apps/ipstore/server.py &
python3 /scp/scrapemeagain/dockerized/apps/healthcheck/test.py $IPSTORE_HOST $IPSTORE_PORT
python3 /scp/scrapemeagain/dockerized/apps/urlbroker/server.py &
python3 /scp/scrapemeagain/dockerized/apps/healthcheck/test.py $URLBROKER_HOST $URLBROKER_PORT
python3 /scp/scrapemeagain/dockerized/apps/datastore/server.py &
python3 /scp/scrapemeagain/dockerized/apps/healthcheck/test.py $DATASTORE_HOST $DATASTORE_PORT
python3 /scp/scrapemeagain/dockerized/apps/healthcheck/server.py &
python3 /scp/scrapemeagain/dockerized/apps/healthcheck/test.py $HEALTHCHECK_HOST $HEALTHCHECK_PORT

# NOTE use `python3 -u <file>` to unbuffer stdout and stderr, e.g. for debugging.
python3 -u /scp/scrapemeagain/scrapers/$SCRAPER_PACKAGE/main_dockerized.py

python3 -c 'from scrapemeagain.dockerized.utils import wait_for_other_scrapers; wait_for_other_scrapers()'

# For dev only, to keep the container up.
# tail -f /dev/null
