from datetime import datetime
import json
import multiprocessing
import os
import subprocess
import tempfile
from time import sleep
import unittest

from sqlalchemy import create_engine
from scrapemeagain.dockerized.utils import get_inf_ip_address
from scrapemeagain.utils.alnum import DATE_FORMAT

from examplescraper.config import Config
from examplescraper.examplesite.app import app as examplesite_app
from tests import REPO_DIR, EXAMPLESCRAPER_DIR
from tests.utils import import_docker_compose


docker_compose = import_docker_compose()


DOCKER_HOST_IP = get_inf_ip_address(Config.DOCKER_INTERFACE_NAME)

USER_AGENTS_FILE = os.path.join(REPO_DIR, "useragents.json")
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

        if not os.path.exists(USER_AGENTS_FILE_BACKUP):
            with open(USER_AGENTS_FILE, "w") as outfile:
                json.dump(FAKE_USER_AGENTS_JSON, outfile)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(USER_AGENTS_FILE_BACKUP):
            os.rename(USER_AGENTS_FILE_BACKUP, USER_AGENTS_FILE)

    def _run_examplesite(self):
        p = multiprocessing.Process(
            target=examplesite_app.run, args=(DOCKER_HOST_IP, 9090)
        )
        p.start()

        return p

    def _run_examplescraper_compose(self):
        scrapemeagain_compose = docker_compose.construct_compose_file(
            EXAMPLESCRAPER_DIR, "tests.integration.fake_config"
        )
        # ' - ' meaning: https://unix.stackexchange.com/a/16364/266262.
        command = "docker-compose -f - up --force-recreate"
        p = subprocess.Popen(command.split(" "), stdin=subprocess.PIPE)
        p.communicate(input=bytes(scrapemeagain_compose, "utf-8"))

    def _get_container_name(self, name_pattern, queue):
        def get_running_container_name(name_pattern, queue):
            command = "docker ps | grep {}".format(name_pattern)
            scraper_name = None

            while scraper_name is None:
                try:
                    out = subprocess.check_output(command, shell=True)
                    out = out.strip()
                    scraper_name = out.split()[-1]
                except subprocess.CalledProcessError:
                    pass

                sleep(1)

            queue.put(scraper_name)

        p = multiprocessing.Process(
            target=get_running_container_name, args=(name_pattern, queue)
        )
        p.start()

        return p

    def _copy_scraper_files(self, container_name, tmp_dir_path):
        command = f"docker cp {container_name}:/tmp/test-examplescraper {tmp_dir_path}"  # noqa
        subprocess.check_call(command.split(" "))

    def validate_db(self, db_path):
        self.assertTrue(os.path.exists(db_path))

        engine = create_engine(f"sqlite:///{db_path}")

        expected_table_name = "example_item_data"
        self.assertIn(expected_table_name, engine.table_names())

        sql = f"SELECT count(*) FROM {expected_table_name}"
        # 100 = 10 list pages * 10 post links per list page.
        self.assertEqual(engine.execute(sql).fetchone()[0], 100)

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

        container_name_queue = multiprocessing.Queue()
        container_name_getter = self._get_container_name(
            "examplescraper-scp1", container_name_queue
        )

        try:
            self._run_examplescraper_compose()
        finally:
            examplesite.terminate()
            examplesite.join()

            container_name_getter.terminate()
            container_name_getter.join()

        with tempfile.TemporaryDirectory() as tmp_dir_path:
            container_name = container_name_queue.get().decode("utf-8")
            self._copy_scraper_files(container_name, tmp_dir_path)

            expected_db_file = os.path.join(
                tmp_dir_path, "test-examplescraper", "example.sqlite"
            )
            self.validate_db(expected_db_file)
