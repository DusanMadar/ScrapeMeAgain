import unittest
from unittest.mock import patch

from tests.utils import import_docker_compose


docker_compose = import_docker_compose()


EXPECTED_EXAMPLESCRAPER_COMPOSE_DICT = {
    "version": "3",
    "services": {
        "examplescraper-scp1": {
            "environment": [
                "SERVICE_NAME_TEMPLATE=examplescraper-scp{}",
                "SERVICE_NAME_MASTER_SCRAPER=examplescraper-scp1",
                "DOCKER_HOST_IP=fake_docker_host_ip",
                "TOR_PORT=9051",
                "TOR_PASSWORD=I-solemnly-swear-I-am-up-to-no-good",
                "PRIVOXY_PORT=8118",
                "PRIVOXY_HOST=127.0.0.1",
                "IPSTORE_PORT=5000",
                "URLBROKER_PORT=6000",
                "DATASTORE_PORT=7000",
                "HEALTHCHECK_PORT=8000",
                "SCRAPER_PACKAGE=examplescraper",
                "SCRAPER_CONFIG=tests.integration.fake_config",
            ],
            "image": "dusanmadar/scrapemeagain:1.1.0",
            "volumes": ["/tmp/examplescraper:/scp/examplescraper"],
            "entrypoint": "/scrapemeagain/scrapemeagain/dockerized/entrypoints/entrypoint.scp1.sh",  # noqa
        },
        "examplescraper-scp2": {
            "environment": [
                "SERVICE_NAME_TEMPLATE=examplescraper-scp{}",
                "SERVICE_NAME_MASTER_SCRAPER=examplescraper-scp1",
                "DOCKER_HOST_IP=fake_docker_host_ip",
                "TOR_PORT=9051",
                "TOR_PASSWORD=I-solemnly-swear-I-am-up-to-no-good",
                "PRIVOXY_PORT=8118",
                "PRIVOXY_HOST=127.0.0.1",
                "IPSTORE_PORT=5000",
                "URLBROKER_PORT=6000",
                "DATASTORE_PORT=7000",
                "HEALTHCHECK_PORT=8000",
                "SCRAPER_PACKAGE=examplescraper",
                "SCRAPER_CONFIG=tests.integration.fake_config",
            ],
            "image": "dusanmadar/scrapemeagain:1.1.0",
            "volumes": ["/tmp/examplescraper:/scp/examplescraper"],
            "depends_on": ["examplescraper-scp1"],
            "entrypoint": "/scrapemeagain/scrapemeagain/dockerized/entrypoints/entrypoint.scpx.sh",  # noqa
        },
    },
}


class DockerComposeTestCase(unittest.TestCase):
    @patch("scrapemeagain-compose.DOCKER_HOST_IP", "fake_docker_host_ip")
    def test_construct_compose_dict(self):
        """
        Test `construct_compose_dict` returns expected compose dict.
        """
        self.assertEqual(
            EXPECTED_EXAMPLESCRAPER_COMPOSE_DICT,
            docker_compose.construct_compose_dict(
                "/tmp/examplescraper", "tests.integration.fake_config"
            ),
        )

    def test_construct_compose_dict_nonexisting_scraper(self):
        """
        Test `construct_compose_dict` raises `ModuleNotFoundError` for a
        nonexisting scraper.
        """
        with self.assertRaises(ModuleNotFoundError):
            docker_compose.construct_compose_dict("/nonexisting")
