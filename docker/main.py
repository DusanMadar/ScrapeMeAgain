"""
Dynamic `docker-compose.yml` based on settings defined in `distributed.config`.

Usesage: python main.py | docker-compose -f - up
"""

import os

import yaml

from scrapemeagain.distributed.config import Config


CONTAINER_SRCDIR = '/scp'  # Must match `SRCDIR` env variable in Dockerfile.
CURENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURENT_DIR)

ENTRYPOINT_PATH_TEMPLATE = CONTAINER_SRCDIR + '/docker/entrypoint.{}.sh'


def create_scraper_service(service_id):
    service_name = 'scp{}'.format(service_id)
    service_settings = {
        'container_name': service_name,
        'environment': [
            'PRIVOXY_HOST={}'.format(Config.PRIVOXY_HOST),
            'PRIVOXY_PORT={}'.format(Config.PRIVOXY_PORT),
            'TOR_PORT={}'.format(Config.TOR_PORT),
            'TOR_PASSWORD={}'.format(Config.TOR_PASSWORD),
        ],
        'hostname': service_name,
        'image': 'scp:latest',
        'volumes': [
            '{}:{}'.format(PARENT_DIR, CONTAINER_SRCDIR),
        ]
    }

    if service_id == 1:
        # Master scraper specific settings.
        entrypoint = ENTRYPOINT_PATH_TEMPLATE.format('scp1')
        service_settings['build'] = {
            'context': PARENT_DIR,
            'dockerfile': os.path.join(PARENT_DIR, 'Dockerfile')
        }
    else:
        # Worker specific settings.
        entrypoint = ENTRYPOINT_PATH_TEMPLATE.format('scpx')
        service_settings['depends_on'] = ['scp{}'.format(service_id - 1)]

    service_settings['entrypoint'] = entrypoint

    return {service_name: service_settings}


if __name__ == '__main__':
    docker_compose = {
        'version': '2',
        'services': {},
    }

    for sraper_id in range(0, Config.SCRAPERS_COUNT):
        sraper_id += 1

        docker_compose['services'].update(create_scraper_service(sraper_id))

    print(yaml.dump(docker_compose))
