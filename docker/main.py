"""
Append `docker-compose.base.yml` based on `.env.scp` settings.

Usesage: python main.py | docker-compose -f - up
"""

import os

from dotenv import load_dotenv
import yaml


CURENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURENT_DIR)

ENV_SCP = os.path.join(CURENT_DIR, '.env.scp')
ENTRYPOINT_PATH_TEMPLATE = '/scp/docker/entrypoint.{}.sh'


def get_scrapers_count():
    load_dotenv(ENV_SCP)

    return int(os.environ.get('SCRAPERS_COUNT'))


def create_scraper_service(service_id):
    service_name = 'scp{}'.format(service_id)
    service_settings = {
        'container_name': service_name,
        'env_file': ENV_SCP,
        'hostname': service_name,
        'image': 'scp:latest',
        'volumes': [
            '{}:/scp'.format(PARENT_DIR),
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

    for s in range(0, get_scrapers_count()):
        s += 1

        docker_compose['services'].update(create_scraper_service(s))

    print(yaml.dump(docker_compose))
