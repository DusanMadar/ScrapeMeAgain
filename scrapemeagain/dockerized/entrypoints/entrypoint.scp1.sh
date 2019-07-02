#!/bin/sh

# NOTE any `python3` process accessing `config.Config` needs to call
# `apply_scraper_config()` in order to use current scraper's config!

# Exit immediately if a command exits with a non-zero status.
set -e

/bin/sh $APP_SRC_DIR/dockerized/entrypoints/entrypoint.base.sh

scraper_main_file=$SCP_DIR/$SCRAPER_PACKAGE/main_dockerized.py

# Ensure `useragents.json` is ready.
python3 -c 'from scrapemeagain.utils.useragents import get_user_agents; get_user_agents("'$scraper_main_file'")'

# Wait for controller process to start.
python3 $APP_SRC_DIR/dockerized/controller/server.py &
python3 $APP_SRC_DIR/dockerized/controller/healthcheck.py

# NOTE use `python3 -u <file>` to unbuffer stdout and stderr, e.g. for debugging.
python3 -u $scraper_main_file

python3 -c 'from scrapemeagain.dockerized.utils import wait_for_other_scrapers; wait_for_other_scrapers()'

# For dev only, to keep the container up.
# tail -f /dev/null
