from scrapemeagain.config import Config


Config.SCRAPERS_COUNT = 2

Config.LOG_LEVEL = "DEBUG"

Config.DATA_DIRECTORY = "/tmp/examplescraper"

Config.URLBROKER_CLASS = (
    "scrapemeagain.scrapers.examplescraper.scraper.ListUrlsBroker"
)
Config.DATASTORE_DATABASER_CLASS = (
    "scrapemeagain.scrapers.examplescraper.databaser.DataStoreDatabaser"
)
