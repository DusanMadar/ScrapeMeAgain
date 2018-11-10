"""
Dynamic `docker-compose.yml` based on settings defined in `config`.

Usage:
    `python3 docker-compose.py -s <scraper> [-c <path.to.config>] | docker-compose -f - up`

    Example:
    $ cd scrapemeagain
    $ python3 docker-compose.py -s examplescraper | docker-compose -f - up
    $ python3 docker-compose.py -s examplescraper -c tests.integration.fake_config | docker-compose -f - up
"""  # noqa

import argparse
import os

import yaml

from scrapemeagain.config import Config
from scrapemeagain.dockerized.utils import (
    apply_scraper_config,
    get_inf_ip_address,
)

CONTAINER_SRCDIR = "/scp"  # Must match `SRCDIR` env variable in Dockerfile.
CURENT_DIR = os.path.dirname(os.path.abspath(__file__))

ENTRYPOINT_PATH_TEMPLATE = (
    CONTAINER_SRCDIR + "/scrapemeagain/dockerized/entrypoints/entrypoint.{}.sh"
)

DOCKER_HOST_IP = get_inf_ip_address(Config.DOCKER_INTERFACE_NAME)


parser = argparse.ArgumentParser()
parser.add_argument(
    "-s",
    "--scraper",
    required=True,
    help="Scraper package name, e.g. 'examplescraper'.",
)
parser.add_argument(
    "-c",
    "--config",
    required=False,
    help="Config module dotted path.",
    default=None,
)


def create_scraper_service(sraper_id, scraper_package, scraper_config):
    service_name_template = "{0}-scp".format(scraper_package)
    service_name_template += "{}"
    # The first scraper service is always the master one.
    service_name_master = service_name_template.format(1)
    service_name = service_name_template.format(sraper_id)

    service_settings = {
        "environment": [
            "SERVICE_NAME_TEMPLATE={}".format(service_name_template),
            "SERVICE_NAME_MASTER_SCRAPER={}".format(service_name_master),
            "DOCKER_HOST_IP={}".format(DOCKER_HOST_IP),
            "TOR_PORT={}".format(Config.TOR_PORT),
            "TOR_PASSWORD={}".format(Config.TOR_PASSWORD),
            "PRIVOXY_PORT={}".format(Config.PRIVOXY_PORT),
            "PRIVOXY_HOST={}".format(Config.PRIVOXY_HOST),
            "IPSTORE_PORT={}".format(Config.IPSTORE_PORT),
            "URLBROKER_PORT={}".format(Config.URLBROKER_PORT),
            "DATASTORE_PORT={}".format(Config.DATASTORE_PORT),
            "HEALTHCHECK_PORT={}".format(Config.HEALTHCHECK_PORT),
            "SCRAPER_PACKAGE={}".format(scraper_package),
        ],
        "image": "scp:latest",
        "volumes": ["{}:{}".format(CURENT_DIR, CONTAINER_SRCDIR)],
    }

    if scraper_config is not None:
        service_settings["environment"].append(
            "SCRAPER_CONFIG={}".format(scraper_config)
        )

    if sraper_id == 1:
        # Master scraper specific settings.
        entrypoint = ENTRYPOINT_PATH_TEMPLATE.format("scp1")
        service_settings["build"] = {
            "context": CURENT_DIR,
            "dockerfile": os.path.join(CURENT_DIR, "Dockerfile"),
        }
    else:
        # Worker specific settings.
        entrypoint = ENTRYPOINT_PATH_TEMPLATE.format("scpx")
        service_settings["depends_on"] = [
            service_name_template.format(sraper_id - 1)
        ]

    service_settings["entrypoint"] = entrypoint

    return {service_name: service_settings}


def construct_compose_dict(scraper_package, scraper_config=None):
    # Apply scraper specific config.
    apply_scraper_config(scraper_package, scraper_config)

    docker_compose = {"version": "3", "services": {}}

    for sraper_id in range(0, Config.SCRAPERS_COUNT):
        sraper_id += 1

        docker_compose["services"].update(
            create_scraper_service(sraper_id, scraper_package, scraper_config)
        )

    return docker_compose


if __name__ == "__main__":
    args = parser.parse_args()
    print(yaml.dump(construct_compose_dict(args.scraper, args.config)))
