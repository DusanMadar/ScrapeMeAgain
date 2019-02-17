#!/usr/bin/env python3


"""
Dynamic `docker-compose.yml` based on settings defined in `config`.

Usage:
    `python3 scrapemeagain-compose.py -s <scraper> [-c <path.to.some.config>] | docker-compose -f - up`

    Example:
    $ cd ../
    $ python3 scripts/scrapemeagain-compose.py -s $(pwd)/examples/examplescraper | docker-compose -f - up
    $ python3 scripts/scrapemeagain-compose.py -s $(pwd)/examples/examplescraper -c tests.integration.fake_config | docker-compose -f - up
"""  # noqa


import argparse
import inspect
import os
import sys

from jinja2 import Template

from scrapemeagain.config import Config
from scrapemeagain.dockerized.utils import (
    apply_scraper_config,
    get_inf_ip_address,
)

# Must match Dockerfile's `SCP_DIR` env variable.
SCP_DIR = "/scp"
# Must match Dockerfile's `APP_SRC_DIR` env variable.
APP_SRC_DIR = "/scrapemeagain/scrapemeagain"
ENTRYPOINT_DIR = os.path.join(APP_SRC_DIR, "dockerized", "entrypoints")
ENTRYPOINT_TEMPLATE = os.path.join(ENTRYPOINT_DIR, "entrypoint.scp{}.sh")
DOCKER_HOST_IP = get_inf_ip_address(Config.DOCKER_INTERFACE_NAME)


def create_scraper_service(id, package, path, config):
    service_name_template = "{}-scp{{}}".format(package)

    return {
        "name": service_name_template.format(id),
        "entrypoint": ENTRYPOINT_TEMPLATE.format(1 if id == 1 else "x"),
        "volumes": ["{}:{}".format(path, os.path.join(SCP_DIR, package))],
        "environment": {
            "DOCKER_HOST_IP": DOCKER_HOST_IP,
            "SCRAPER_PACKAGE": package,
            "SCRAPER_CONFIG": config,
            "SERVICE_NAME_TEMPLATE": service_name_template,
            # The first scraper service is always the master one.
            "SERVICE_NAME_MASTER_SCRAPER": service_name_template.format(1),
            "TOR_PORT": Config.TOR_PORT,
            "TOR_PASSWORD": Config.TOR_PASSWORD,
            "PRIVOXY_PORT": Config.PRIVOXY_PORT,
            "PRIVOXY_HOST": Config.PRIVOXY_HOST,
            "IPSTORE_PORT": Config.IPSTORE_PORT,
            "URLBROKER_PORT": Config.URLBROKER_PORT,
            "DATASTORE_PORT": Config.DATASTORE_PORT,
            "HEALTHCHECK_PORT": Config.HEALTHCHECK_PORT,
        },
    }


def construct_compose_file(path, config=None):
    # Apply scraper specific config (but first ensure it's accessible).
    sys.path.insert(0, os.path.dirname(path))
    package = path.split(os.sep)[-1]
    apply_scraper_config(package, config)

    services = [
        create_scraper_service(id, package, path, config)
        for id in range(1, Config.SCRAPERS_COUNT + 1)
    ]

    # A dynamic way to get the path of `scrapemeagain.dockerized` package.
    # Required because this file must be runnable both during development and
    # after installing the package.
    # Credits: https://stackoverflow.com/q/2419416/4183498.
    dockerized_utils_module_path = inspect.getsourcefile(apply_scraper_config)
    template_dir = os.path.dirname(dockerized_utils_module_path)
    with open(os.path.join(template_dir, "docker-compose.yml")) as f:
        template = Template(f.read())

    return template.render(services=services).strip()


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
    print(construct_compose_file(args.scraper, args.config))


if __name__ == "__main__":
    main()
