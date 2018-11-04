from datetime import datetime
import json
import multiprocessing
import os
import subprocess
import tempfile
from time import sleep
import unittest
import yaml

from sqlalchemy import create_engine

from scrapemeagain.dockerized.utils import get_inf_ip_address
from scrapemeagain.scrapers.examplescraper.config import Config
from scrapemeagain.scrapers.examplescraper.examplesite.app import app
from scrapemeagain.utils.alnum import DATE_FORMAT

docker_compose = __import__("docker-compose")


DOCKER_HOST_IP = get_inf_ip_address(Config.DOCKER_INTERFACE_NAME)

USER_AGENTS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "useragents.json",
)
USER_AGENTS_FILE_BACKUP = USER_AGENTS_FILE + ".bak"

FAKE_USER_AGENTS_JSON = {
    "date": datetime.today().strftime(DATE_FORMAT),
    "useragents": ["User Agent 1", "User Agent 2", "User Agent 3"],
}


class IntegrationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Prevent populating useragents file.
        if os.path.exists(USER_AGENTS_FILE):
            os.rename(USER_AGENTS_FILE, USER_AGENTS_FILE_BACKUP)

        with open(USER_AGENTS_FILE, "w") as outfile:
            json.dump(FAKE_USER_AGENTS_JSON, outfile)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(USER_AGENTS_FILE_BACKUP):
            os.rename(USER_AGENTS_FILE_BACKUP, USER_AGENTS_FILE)

    def _run_examplesite(self):
        p = multiprocessing.Process(
            target=app.run, args=(DOCKER_HOST_IP, 9090)
        )
        p.start()

        return p

    def _run_examplescraper_compose(self):
        compose_file = yaml.dump(
            docker_compose.construct_compose_dict(
                "examplescraper", "tests.integration.fake_config"
            )
        )
        # ' - ' meaning: https://unix.stackexchange.com/a/16364/266262.
        command = "docker-compose -f - up --force-recreate"
        p = subprocess.Popen(command.split(" "), stdin=subprocess.PIPE)
        p.communicate(input=bytes(compose_file, "utf-8"))

    def _copy_scraper_files(self, tmp_dir_path):
        command = f"docker cp scp1:/tmp/test-examplescraper {tmp_dir_path}"
        subprocess.check_call(command.split(" "))

    def validate_db(self, db_path):
        self.assertTrue(os.path.exists(db_path))

        engine = create_engine(f"sqlite:///{db_path}")

        expected_table_name = "example_item_data"
        self.assertIn(expected_table_name, engine.table_names())

        sql = f"SELECT count(*) FROM {expected_table_name}"
        # 1100 = 110 list pages * 10 post links per list page.
        self.assertEqual(engine.execute(sql).fetchone()[0], 1100)

    def test_examplescraper_works(self):
        """
        Test `examplescraper` can scrape required data from `examplesite`.
        """
        examplesite = self._run_examplesite()
        # TODO there has to a better way to wait till the process has started.
        sleep(1)
        if not examplesite.is_alive():
            print("Failed to start examplesite")
            return

        try:
            self._run_examplescraper_compose()
        finally:
            examplesite.terminate()
            examplesite.join()

        with tempfile.TemporaryDirectory() as tmp_dir_path:
            self._copy_scraper_files(tmp_dir_path)

            expected_db_file = os.path.join(
                tmp_dir_path, "test-examplescraper", "example.sqlite"
            )
            self.validate_db(expected_db_file)
