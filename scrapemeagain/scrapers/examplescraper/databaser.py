from scrapemeagain import databaser

from scrapemeagain.scrapers.examplescraper.scraper import ExampleScraper


class DataStoreDatabaser(databaser.DataStoreDatabaser):
    def __init__(self):
        super().__init__(ExampleScraper.db_file, ExampleScraper.db_table)


class DockerizedDatabaser(databaser.DockerizedDatabaser):
    pass
