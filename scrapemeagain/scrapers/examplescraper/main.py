from toripchanger import TorIpChanger

from config import Config
from scrapemeagain.databaser import Databaser
from scrapemeagain.pipeline import Pipeline
from scrapemeagain.scrapers.examplescraper.scraper import ExampleScraper
from scrapemeagain.utils import services
from scrapemeagain.utils.logger import setup_logging
from scrapemeagain.utils.useragents import get_user_agents


# Configure TorIpChanger.
tor_ip_changer = TorIpChanger(
    reuse_threshold=Config.REUSE_THRESHOLD,
    local_http_proxy=Config.LOCAL_HTTP_PROXY,
    tor_password=Config.TOR_PASSWORD,
    tor_port=Config.TOR_PORT,
    new_ip_max_attempts=Config.NEW_IP_MAX_ATTEMPTS
)

# Configure useragents.
Config.USER_AGENTS = get_user_agents()

# Configure logging.
setup_logging(logger_name='example-scraper')


# Prepare the scraping pipeline.
scraper = ExampleScraper()
databaser = Databaser(scraper.db_file, scraper.db_table)
pipeline = Pipeline(scraper, databaser, tor_ip_changer)
pipeline.prepare_multiprocessing()

try:
    services.start_backbone_services()

    # Change IP before starting.
    pipeline.tor_ip_changer.get_new_ip()

    # Collect item URLs.
    pipeline.get_item_urls()

    # Collect item properties.
    pipeline.get_item_properties()
finally:
    services.stop_backbone_services()
