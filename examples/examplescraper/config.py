from scrapemeagain.config import Config

Config.REUSE_THRESHOLD = 1

Config.SCRAPERS_COUNT = 2

Config.LOG_LEVEL = "DEBUG"

Config.DATA_DIRECTORY = "/tmp/examplescraper"

Config.URLBROKER_CLASS = "examplescraper.scraper.ListUrlsBroker"
Config.DATASTORE_DATABASER_CLASS = (
    "examplescraper.databaser.DataStoreDatabaser"
)
