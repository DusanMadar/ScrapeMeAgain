import os


class Config(object):
    #
    # General settings.
    # Where to place the *.sqlite DB file populated with scraped data.
    DATA_DIRECTORY = os.environ.get('SCRAPER_DATA_DIRECTORY')

    # Log level settings.
    # NOTE 'DEBUG' will be very verbose.
    LOG_LEVEL = os.environ.get('SCRAPER_LOG_LEVEL')

    # How often data (how many items at once) should be commited to the DB.
    TRANSACTION_SIZE = os.environ.get('SCRAPER_TRANSACTION_SIZE')

    #
    # Scraping settings.
    # Number of processes used to asynchronously scrape data from URLs.
    SCRAPE_PROCESSES = os.environ.get('SCRAPER_SCRAPE_PROCESSES')

    # How long to wait for a response (in seconds).
    REQUEST_TIMEOUT = os.environ.get('SCRAPER_REQUEST_TIMEOUT')

    # User agents to use in requests.
    # NOTE must be populated before starting the scraping process.
    # TODO Should be created once for all scraper containers.
    USER_AGENTS = None

    #
    # TorIpChanger settings.
    LOCAL_HTTP_PROXY = '{0}:{1}'.format(
        os.environ.get('PRIVOXY_HOST'), os.environ.get('PRIVOXY_PORT')
    )
    NEW_IP_MAX_ATTEMPTS = os.environ.get('IPCHANGER_NEW_IP_MAX_ATTEMPTS')
    REUSE_THRESHOLD = os.environ.get('IPSTORE_REUSE_THRESHOLD')
    TOR_PORT = os.environ.get('TOR_PORT')
    TOR_PASSWORD = os.environ.get('TOR_PASSWORD')
