from scrapemeagain.config import Config
from scrapemeagain.dockerized.utils import (
    apply_scraper_config,
    get_class_from_path,
)
from scrapemeagain.pipeline import DockerizedPipeline
from scrapemeagain.utils.logger import setup_logging
from scrapemeagain.utils.useragents import get_user_agents

from examplescraper.databaser import DockerizedDatabaser
from examplescraper.scraper import DockerizedExampleScraper


# Update config, setup logging and useragents.
apply_scraper_config()
setup_logging(logger_name="examplescraper")
Config.USER_AGENTS = get_user_agents()


# Configure DockerizedTorIpChanger.
toripchanger_class = get_class_from_path(Config.TORIPCHANGER_CLASS)
tor_ip_changer = toripchanger_class(
    local_http_proxy=Config.LOCAL_HTTP_PROXY,
    tor_password=Config.TOR_PASSWORD,
    tor_port=Config.TOR_PORT,
    new_ip_max_attempts=Config.NEW_IP_MAX_ATTEMPTS,
)


# Prepare the scraping pipeline.
scraper = DockerizedExampleScraper()
databaser = DockerizedDatabaser(scraper.db_file)
pipeline = DockerizedPipeline(scraper, databaser, tor_ip_changer)
pipeline.prepare_multiprocessing()


if __name__ == "__main__":
    # Change IP before starting.
    pipeline.tor_ip_changer.get_new_ip()

    # Collect item URLs.
    pipeline.get_item_urls()

    # Collect item properties.
    pipeline.get_item_properties()
