from scrapemeagain.config import Config

# The 2 configs below are for test purposes only. Normally there's no need for
# any changes to `LOCAL_HTTP_PROXY` or `TORIPCHANGER_CLASS`.
Config.LOCAL_HTTP_PROXY = ""
Config.TORIPCHANGER_CLASS = (
    "scrapemeagain.dockerized.ipchanger.TestFriendlyDockerizedTorIpChanger"
)

Config.SCRAPERS_COUNT = 2

Config.LOG_LEVEL = "DEBUG"

Config.DATA_DIRECTORY = "/tmp/examplescraper"

Config.URLBROKER_CLASS = (
    "scrapemeagain.scrapers.examplescraper.scraper.ListUrlsBroker"
)
Config.DATASTORE_DATABASER_CLASS = (
    "scrapemeagain.scrapers.examplescraper.databaser.DataStoreDatabaser"
)
