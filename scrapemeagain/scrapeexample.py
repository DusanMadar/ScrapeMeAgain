from scrapemeagain.databaser import Databaser
from scrapemeagain.pipeline import Pipeline
from scrapemeagain.scrapers import ExampleScraper

scraper = ExampleScraper()
databaser = Databaser(scraper.db_file, scraper.db_table)

pipeline = Pipeline(scraper, databaser)
pipeline.prepare_dependencies()
pipeline.prepare_multiprocessing()
pipeline.tor_ip_changer.get_new_ip()

pipeline.get_item_urls()
