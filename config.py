import os


class Config(object):
    #
    # General settings.
    # Where to place the *.sqlite DB file populated with scraped data.
    DATA_DIRECTORY = '/tmp'

    # Log level settings.
    # NOTE 'DEBUG' will be very verbose.
    LOG_LEVEL = 'WARNING'

    # How often data (how many items at once) should be commited to the DB.
    TRANSACTION_SIZE = 5000

    #
    # Scraping settings.
    # Number of processes used to asynchronously scrape data from URLs.
    SCRAPE_PROCESSES = 5

    # How long to wait for a response (in seconds).
    REQUEST_TIMEOUT = 10

    # User agents to use in requests.
    # NOTE must be populated before starting the scraping process.
    USER_AGENTS = None

    #
    # TorIpChanger settings.
    LOCAL_HTTP_PROXY = '127.0.0.1:8118'
    NEW_IP_MAX_ATTEMPTS = 1000
    REUSE_THRESHOLD = 10
    TOR_PASSWORD = (
        os.environ.get('TOR_PASSWORD', None) or 'put your password here'
    )
    TOR_PORT = 9051
