from toripchanger import TorIpChanger

import config
from scrapemeagain.databaser import Databaser
from scrapemeagain.pipeline import Pipeline
from scrapemeagain.scrapers import ExampleScraper

scraper = ExampleScraper()
databaser = Databaser(scraper.db_file, scraper.db_table)
tor_ip_changer = TorIpChanger(
    reuse_threshold=config.REUSE_THRESHOLD,
    local_http_proxy=config.LOCAL_HTTP_PROXY,
    tor_password=config.TOR_PASSWORD,
    tor_port=config.TOR_PORT,
    new_ip_max_attempts=config.NEW_IP_MAX_ATTEMPTS
)

pipeline = Pipeline(scraper, databaser, tor_ip_changer)
pipeline.prepare_multiprocessing()
pipeline.tor_ip_changer.get_new_ip()

pipeline.get_item_urls()
