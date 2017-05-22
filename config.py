import os

#
# General settings.
# This directory will be populated with scraped data.
DATA_DIRECTORY = '/tmp'

# Log level settings (NOTE 'debug' will be very verbose).
LOG_LEVEL = 'WARNING'

#
# Scraping settings.
# Number asynchronously scraped URLs.
SCRAPE_PROCESSES = 5
# How long to wait for a response (is seconds).
REQUEST_TIMEOUT = 5

# TorIpChanger settings.
LOCAL_HTTP_PROXY = '127.0.0.1:8118'
NEW_IP_MAX_ATTEMPTS = 1000
REUSE_THRESHOLD = 10
TOR_PASSWORD = os.environ.get('TOR_PASSWORD', None) or 'put your password here'
TOR_PORT = 9051
