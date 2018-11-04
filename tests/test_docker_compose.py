import unittest


docker_compose = __import__("docker-compose")


class DockerComposeTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Dirty way to mock `DOCKER_HOST_IP`.
        cls.original_docker_host_ip = docker_compose.DOCKER_HOST_IP
        docker_compose.DOCKER_HOST_IP = "fake_docker_host_ip"

    @classmethod
    def tearDownClass(cls):
        docker_compose.DOCKER_HOST_IP = cls.original_docker_host_ip

    def test_construct_compose_dict(self):
        """
        Test `construct_compose_dict` returns expected compose dict.
        """
        expected_examplescraper_compose_dict = {
            "version": "3",
            "services": {
                "scp1": {
                    "container_name": "scp1",
                    "environment": [
                        "TOR_PORT=9051",
                        "TOR_PASSWORD=I-solemnly-swear-I-am-up-to-no-good",
                        "PRIVOXY_PORT=8118",
                        "PRIVOXY_HOST=127.0.0.1",
                        "IPSTORE_PORT=5000",
                        "IPSTORE_HOST=scp1",
                        "URLBROKER_PORT=6000",
                        "URLBROKER_HOST=scp1",
                        "DATASTORE_PORT=7000",
                        "DATASTORE_HOST=scp1",
                        "HEALTHCHECK_PORT=8000",
                        "HEALTHCHECK_HOST=scp1",
                        "SCRAPER_PACKAGE=examplescraper",
                        "DOCKER_HOST_IP=fake_docker_host_ip",
                        "SCRAPER_CONFIG=tests.integration.fake_config",
                    ],
                    "hostname": "scp1",
                    "image": "scp:latest",
                    "volumes": ["/home/dm/code/scrapemeagain:/scp"],
                    "build": {
                        "context": "/home/dm/code/scrapemeagain",
                        "dockerfile": "/home/dm/code/scrapemeagain/Dockerfile",
                    },
                    "entrypoint": "/scp/scrapemeagain/dockerized/entrypoints/entrypoint.scp1.sh",
                },
                "scp2": {
                    "container_name": "scp2",
                    "environment": [
                        "TOR_PORT=9051",
                        "TOR_PASSWORD=I-solemnly-swear-I-am-up-to-no-good",
                        "PRIVOXY_PORT=8118",
                        "PRIVOXY_HOST=127.0.0.1",
                        "IPSTORE_PORT=5000",
                        "IPSTORE_HOST=scp1",
                        "URLBROKER_PORT=6000",
                        "URLBROKER_HOST=scp1",
                        "DATASTORE_PORT=7000",
                        "DATASTORE_HOST=scp1",
                        "HEALTHCHECK_PORT=8000",
                        "HEALTHCHECK_HOST=scp1",
                        "SCRAPER_PACKAGE=examplescraper",
                        "DOCKER_HOST_IP=fake_docker_host_ip",
                        "SCRAPER_CONFIG=tests.integration.fake_config",
                    ],
                    "hostname": "scp2",
                    "image": "scp:latest",
                    "volumes": ["/home/dm/code/scrapemeagain:/scp"],
                    "depends_on": ["scp1"],
                    "entrypoint": "/scp/scrapemeagain/dockerized/entrypoints/entrypoint.scpx.sh",
                },
            },
        }

        self.assertEqual(
            expected_examplescraper_compose_dict,
            docker_compose.construct_compose_dict(
                "examplescraper", "tests.integration.fake_config"
            ),
        )

    def test_construct_compose_dict_nonexisting_scraper(self):
        """
        Test `construct_compose_dict` raises `ModuleNotFoundError` for a\
        nonexisting scraper.
        """
        with self.assertRaises(ModuleNotFoundError):
            docker_compose.construct_compose_dict("nonexisting")
