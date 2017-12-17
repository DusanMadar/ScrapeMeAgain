"""
Append `docker-compose.base.yml` based on `.env.scp` settings.

Usesage: python main.py | docker-compose -f - up
"""

import os

from dotenv import load_dotenv
import yaml


ENV_SCP = '.env.scp'
DOCKER_COMPOSE_BASE = 'docker-compose.base.yml'


def get_scrapers_count():
    load_dotenv(ENV_SCP)

    return int(os.environ.get('SCRAPERS_COUNT'))


def get_docker_compose_base():
    with open(DOCKER_COMPOSE_BASE, 'r') as f:
        return yaml.load(f)


def create_scraper_service(service_id):
    service_name = 'scp{}'.format(service_id)
    service_settings = {
        'container_name': service_name,
        'depends_on': ['scp{}'.format(service_id - 1)],
        'entrypoint': '/scp/entrypoint.scpx.sh',
        'env_file': ENV_SCP,
        'hostname': service_name,
        'image': 'scp:latest',
    }

    return {service_name: service_settings}


if __name__ == '__main__':
    docker_compose = get_docker_compose_base()

    for s in range(0, get_scrapers_count()):
        s += 1

        # Main/master service/scraper is already configured.
        if s == 1:
            continue

        docker_compose['services'].update(create_scraper_service(s))

    print(yaml.dump(docker_compose))
