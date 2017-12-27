from scrapemeagain.config import Config as BaseConfig


class Config(BaseConfig):
    #
    # Orchestration.
    SCRAPERS_COUNT = 2
    MASTER_SCRAPER = 'scp1'

    #
    # IpStore.
    IPSTORE_PORT = 5000
    IPSTORE_HOST = MASTER_SCRAPER
    REUSE_THRESHOLD = BaseConfig.REUSE_THRESHOLD * SCRAPERS_COUNT

    #
    # Controller.
    CONTROLLER_PORT = 6000
    CONTROLLER_HOST = MASTER_SCRAPER
    CONTROLLER_CLASS = (
        'scrapemeagain.scrapers.<package-name>.scraper.<class-name>'
    )
