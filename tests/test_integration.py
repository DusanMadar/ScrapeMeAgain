import json
from datetime import datetime
import os
import unittest

from scrapemeagain.utils.alnum import DATE_FORMAT


USER_AGENTS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "useragents.json"
)
USER_AGENTS_FILE_BACKUP = USER_AGENTS_FILE + ".bak"

FAKE_USER_AGENTS_JSON = {
    "date": datetime.today().strftime(DATE_FORMAT),
    "useragents": ["User Agent 1", "User Agent 2", "User Agent 3"],
}


class IntegrationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(USER_AGENTS_FILE):
            os.rename(USER_AGENTS_FILE, USER_AGENTS_FILE_BACKUP)

        with open(USER_AGENTS_FILE, "w") as outfile:
            json.dump(FAKE_USER_AGENTS_JSON, outfile)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(USER_AGENTS_FILE_BACKUP):
            os.rename(USER_AGENTS_FILE_BACKUP, USER_AGENTS_FILE)

    def test_it_works(self):
        pass
