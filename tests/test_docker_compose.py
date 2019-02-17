import unittest
from unittest.mock import patch

from tests.utils import import_docker_compose


docker_compose = import_docker_compose()


EXPECTED_EXAMPLESCRAPER_COMPOSE = """
version: '3'
services:
  examplescraper-scp1:
    image: dusanmadar/scrapemeagain:1.0.3
    entrypoint: /scrapemeagain/scrapemeagain/dockerized/entrypoints/entrypoint.scp1.sh
    volumes:
      - /tmp/examplescraper:/scp/examplescraper
    environment:
      - DOCKER_HOST_IP=fake_docker_host_ip
      - SCRAPER_PACKAGE=examplescraper
      - SCRAPER_CONFIG=tests.integration.fake_config
      - SERVICE_NAME_TEMPLATE=examplescraper-scp{}
      - SERVICE_NAME_MASTER_SCRAPER=examplescraper-scp1
      - TOR_PORT=9051
      - TOR_PASSWORD=I-solemnly-swear-I-am-up-to-no-good
      - PRIVOXY_PORT=8118
      - PRIVOXY_HOST=127.0.0.1
      - IPSTORE_PORT=5000
      - URLBROKER_PORT=6000
      - DATASTORE_PORT=7000
      - HEALTHCHECK_PORT=8000
  examplescraper-scp2:
    image: dusanmadar/scrapemeagain:1.0.3
    entrypoint: /scrapemeagain/scrapemeagain/dockerized/entrypoints/entrypoint.scpx.sh
    volumes:
      - /tmp/examplescraper:/scp/examplescraper
    environment:
      - DOCKER_HOST_IP=fake_docker_host_ip
      - SCRAPER_PACKAGE=examplescraper
      - SCRAPER_CONFIG=tests.integration.fake_config
      - SERVICE_NAME_TEMPLATE=examplescraper-scp{}
      - SERVICE_NAME_MASTER_SCRAPER=examplescraper-scp1
      - TOR_PORT=9051
      - TOR_PASSWORD=I-solemnly-swear-I-am-up-to-no-good
      - PRIVOXY_PORT=8118
      - PRIVOXY_HOST=127.0.0.1
      - IPSTORE_PORT=5000
      - URLBROKER_PORT=6000
      - DATASTORE_PORT=7000
      - HEALTHCHECK_PORT=8000
""".strip()


class DockerComposeTestCase(unittest.TestCase):
    @patch("scrapemeagain-compose.DOCKER_HOST_IP", "fake_docker_host_ip")
    def test_construct_compose_file(self):
        """
        Test `construct_compose_file` returns expected yaml.
        """
        self.assertEqual(
            EXPECTED_EXAMPLESCRAPER_COMPOSE,
            docker_compose.construct_compose_file(
                "/tmp/examplescraper", "tests.integration.fake_config"
            ),
        )

    def test_construct_compose_file_no_extra_config(self):
        """
        Test `construct_compose_file` returns expected yaml without
        `SCRAPER_CONFIG` env when no extra config is provided.
        """
        yml = docker_compose.construct_compose_file("/tmp/examplescraper")
        self.assertNotIn("SCRAPER_CONFIG", yml)

    def test_construct_compose_file_nonexisting_scraper(self):
        """
        Test `construct_compose_file` raises `ModuleNotFoundError` for a
        nonexisting scraper.
        """
        with self.assertRaises(ModuleNotFoundError):
            docker_compose.construct_compose_file("/nonexisting")
