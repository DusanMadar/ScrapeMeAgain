class Config:
    #
    # General settings.
    # Where to place the *.sqlite DB file populated with scraped data.
    DATA_DIRECTORY = "/tmp"

    # Log level settings.
    # NOTE 'DEBUG' will be very verbose.
    LOG_LEVEL = "WARNING"

    # How often data (how many items at once) should be commited to the DB.
    TRANSACTION_SIZE = 5000

    #
    # Scraping settings.
    # Number of threads used to asynchronously scrape data from URLs.
    WORKERS_COUNT = 50

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
    TOR_PASSWORD = "I-solemnly-swear-I-am-up-to-no-good"

    #
    # Privoxy.
    PRIVOXY_PORT = 8118
    PRIVOXY_HOST = "127.0.0.1"

    #
    # TorIpChanger.
    LOCAL_HTTP_PROXY = "{0}:{1}".format(PRIVOXY_HOST, PRIVOXY_PORT)
    NEW_IP_MAX_ATTEMPTS = 1000
    REUSE_THRESHOLD = 10
    TORIPCHANGER_CLASS = (
        "scrapemeagain.dockerized.ipchanger.DockerizedTorIpChanger"
    )

    # =========================================================================
    # DOCKERIZED SETTINGS.
    # =========================================================================

    DOCKER_INTERFACE_NAME = "docker0"

    #
    # Orchestration.
    SCRAPERS_COUNT = 1
    CONTROLLER_PORT = 5000

    #
    # IpStore.
    IPSTORE_REUSE_THRESHOLD = REUSE_THRESHOLD * SCRAPERS_COUNT

    #
    # URLBroker.
    # NOTE each scraper MUST set a custom `ListUrlsBroker` subclass in
    # 'scrapemeagain.scrapers.{your scraper}.config.URLBROKER_CLASS'
    URLBROKER_CLASS = (
        "scrapemeagain.dockerized.controller.urlbrokers.ListUrlsBroker"
    )

    #
    # DataStore.
    # NOTE set 'scrapemeagain.scrapers.{your scraper}.config.DATASTORE_CLASS'
    # if your scraper adds custom functionality to `DataStoreDatabaser`.
    DATASTORE_DATABASER_CLASS = "scrapemeagain.databaser.DataStoreDatabaser"
