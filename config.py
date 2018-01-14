class Config:
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

    # =========================================================================
    # DEFAULT SERVICES SETTINGS: MUST MATCH HOST SETTINGS.
    # =========================================================================

    #
    # Tor.
    TOR_PORT = 9051
    TOR_PASSWORD = 'I-solemnly-swear-I-am-up-to-no-good'

    #
    # Privoxy.
    PRIVOXY_PORT = 8118
    PRIVOXY_HOST = '127.0.0.1'

    #
    # TorIpChanger.
    LOCAL_HTTP_PROXY = '{0}:{1}'.format(PRIVOXY_HOST, PRIVOXY_PORT)
    NEW_IP_MAX_ATTEMPTS = 1000
    REUSE_THRESHOLD = 10

    # =========================================================================
    # DOCKERIZED SETTINGS.
    # =========================================================================

    #
    # Orchestration.
    SCRAPERS_COUNT = 2
    MASTER_SCRAPER = 'scp1'

    #
    # IpStore.
    IPSTORE_PORT = 5000
    IPSTORE_HOST = MASTER_SCRAPER
    IPSTORE_REUSE_THRESHOLD = REUSE_THRESHOLD * SCRAPERS_COUNT

    #
    # URLBroker.
    URLBROKER_PORT = 6000
    URLBROKER_HOST = MASTER_SCRAPER

    #
    # Healthcheck.
    HEALTHCHECK_PORT = 7000
    HEALTHCHECK_HOST = MASTER_SCRAPER
