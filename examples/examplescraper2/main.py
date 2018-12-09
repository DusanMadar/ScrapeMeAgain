from toripchanger import TorIpChanger

from scrapemeagain.config import Config
from scrapemeagain.databaser import Databaser
from scrapemeagain.scrapers.examplescraper2.custom_pipeline import (
    ExhaustApiLimitPipeLine,
)  # noqa
from scrapemeagain.scrapers.examplescraper2.scraper import ExampleScraper2
from scrapemeagain.utils import services
from scrapemeagain.utils.logger import setup_logging
from scrapemeagain.utils.useragents import get_user_agents


# Configure TorIpChanger.
tor_ip_changer = TorIpChanger(
    reuse_threshold=0,  # We need to remember all exhausted IPs.
    local_http_proxy=Config.LOCAL_HTTP_PROXY,
    tor_password=Config.TOR_PASSWORD,
    tor_port=Config.TOR_PORT,
    new_ip_max_attempts=Config.NEW_IP_MAX_ATTEMPTS,
)

# Configure useragents.
Config.USER_AGENTS = get_user_agents()

# Configure logging.
setup_logging(logger_name="example-scraper2")


# Prepare the scraping pipeline.
scraper = ExampleScraper2()
databaser = Databaser(scraper.db_file, scraper.db_table)
pipeline = ExhaustApiLimitPipeLine(scraper, databaser, tor_ip_changer)
pipeline.prepare_multiprocessing()

try:
    services.start_backbone_services()

    # Change IP before starting.
    pipeline.tor_ip_changer.get_new_ip()

    # Collect item properties.
    pipeline.get_item_properties()
finally:
    services.stop_backbone_services()
