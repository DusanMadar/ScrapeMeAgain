#!/usr/bin/env python3


"""
Dynamic `docker-compose.yml` based on settings defined in `config`.

Usage:
    `python3 scrapemeagain-compose.py -s <scraper> [-c <path.to.some.config>] | docker-compose -f - up`

    Example:
    $ cd ../
    $ python3 scrapemeagain-compose.py -s $(pwd)/examples/examplescraper | docker-compose -f - up
    $ python3 scrapemeagain-compose.py -s $(pwd)/examples/examplescraper -c tests.integration.fake_config | docker-compose -f - up
"""  # noqa


import argparse
import os
import sys

import yaml

from scrapemeagain.config import Config
from scrapemeagain.dockerized.utils import (
    apply_scraper_config,
    get_inf_ip_address,
)

# Must match Dockerfile's `SCP_DIR` env variable.
SCP_DIR = "/scp"
# Must match Dockerfile's `APP_SRC_DIR` env variable.
APP_SRC_DIR = "/scrapemeagain/scrapemeagain"

ENTRYPOINT_PATH_TEMPLATE = (
    APP_SRC_DIR + "/dockerized/entrypoints/entrypoint.{}.sh"
)


DOCKER_HOST_IP = get_inf_ip_address(Config.DOCKER_INTERFACE_NAME)


def create_scraper_service(
    sraper_id, scraper_package, scraper_path, scraper_config
):
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
        "image": "dusanmadar/scrapemeagain:1.1.0",
        "volumes": [
            "{}:{}".format(
                scraper_path, os.path.join(SCP_DIR, scraper_package)
            )
        ],
    }

    if scraper_config is not None:
        service_settings["environment"].append(
            "SCRAPER_CONFIG={}".format(scraper_config)
        )

    if sraper_id == 1:
        # Master scraper specific settings.
        entrypoint = ENTRYPOINT_PATH_TEMPLATE.format("scp1")
    else:
        # Worker specific settings.
        entrypoint = ENTRYPOINT_PATH_TEMPLATE.format("scpx")
        service_settings["depends_on"] = [
            service_name_template.format(sraper_id - 1)
        ]

    service_settings["entrypoint"] = entrypoint

    return {service_name: service_settings}


def construct_compose_dict(scraper_path, scraper_config=None):
    # Apply scraper specific config.
    scraper_package = scraper_path.split(os.sep)[-1]
    prepare_for_apply_scraper_config(scraper_path)
    apply_scraper_config(scraper_package, scraper_config)

    docker_compose = {"version": "3", "services": {}}

    for sraper_id in range(0, Config.SCRAPERS_COUNT):
        sraper_id += 1

        docker_compose["services"].update(
            create_scraper_service(
                sraper_id, scraper_package, scraper_path, scraper_config
            )
        )

    return docker_compose


def prepare_for_apply_scraper_config(scraper_path):
    sys.path.insert(0, os.path.dirname(scraper_path))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "--scraper",
        required=True,
        help=(
            "Absolute path to scraper package dir; e.g. '/tmp/examplescraper'."
        ),
    )
    parser.add_argument(
        "-c",
        "--config",
        required=False,
        help=(
            "Dotted path to a specific (not 'config.py') config module; "
            "e.g. 'examplescraper.more_configs.test_config'. The path must be"
            "importbale locally and in the container."
        ),
        default=None,
    )

    args = parser.parse_args()
    print(yaml.dump(construct_compose_dict(args.scraper, args.config)))


if __name__ == "__main__":
    main()
