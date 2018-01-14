"""
Dynamic `docker-compose.yml` based on settings defined in `config`.

Usage:
    `python3 docker/docker-compose.py <scraper> | docker-compose -f - up`

    Example:
    $ cd scrapemeagain
    $ python3 docker/docker-compose.py examplescraper | docker-compose -f - up
"""

import os
import sys

import yaml

from config import Config


CONTAINER_SRCDIR = '/scp'  # Must match `SRCDIR` env variable in Dockerfile.
CURENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURENT_DIR)

ENTRYPOINT_PATH_TEMPLATE = CONTAINER_SRCDIR + '/docker/entrypoint.{}.sh'


def create_scraper_service(sraper_id, scraper_package):
    service_name = 'scp{}'.format(sraper_id)
    service_settings = {
        'container_name': service_name,
        'environment': [
            'TOR_PORT={}'.format(Config.TOR_PORT),
            'TOR_PASSWORD={}'.format(Config.TOR_PASSWORD),

            'PRIVOXY_PORT={}'.format(Config.PRIVOXY_PORT),
            'PRIVOXY_HOST={}'.format(Config.PRIVOXY_HOST),

            'IPSTORE_PORT={}'.format(Config.IPSTORE_PORT),
            'IPSTORE_HOST={}'.format(Config.IPSTORE_HOST),

            'URLBROKER_PORT={}'.format(Config.URLBROKER_PORT),
            'URLBROKER_HOST={}'.format(Config.URLBROKER_HOST),

            'HEALTHCHECK_PORT={}'.format(Config.HEALTHCHECK_PORT),
            'HEALTHCHECK_HOST={}'.format(Config.HEALTHCHECK_HOST),

            'SCRAPER_PACKAGE={}'.format(scraper_package),
        ],
        'hostname': service_name,
        'image': 'scp:latest',
        'volumes': [
            '{}:{}'.format(PARENT_DIR, CONTAINER_SRCDIR),
        ]
    }

    if sraper_id == 1:
        # Master scraper specific settings.
        entrypoint = ENTRYPOINT_PATH_TEMPLATE.format('scp1')
        service_settings['build'] = {
            'context': PARENT_DIR,
            'dockerfile': os.path.join(PARENT_DIR, 'Dockerfile')
        }
    else:
        # Worker specific settings.
        entrypoint = ENTRYPOINT_PATH_TEMPLATE.format('scpx')
        service_settings['depends_on'] = ['scp{}'.format(sraper_id - 1)]

    service_settings['entrypoint'] = entrypoint

    return {service_name: service_settings}


if __name__ == '__main__':
    try:
        scraper_package = sys.argv[1]
    except IndexError:
        sys.exit('Please provide a scraper name to {}'.format(__file__))

    docker_compose = {
        'version': '3',
        'services': {},
    }

    for sraper_id in range(0, Config.SCRAPERS_COUNT):
        sraper_id += 1

        docker_compose['services'].update(
            create_scraper_service(sraper_id, scraper_package)
        )

    print(yaml.dump(docker_compose))
