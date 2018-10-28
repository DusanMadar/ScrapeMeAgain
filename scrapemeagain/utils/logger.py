"""Global logging setup."""


import logging
import os

import requests

from scrapemeagain.config import Config
from scrapemeagain.utils.alnum import get_current_date


def setup_logging(logger_name):
    # Ensure log dir exists.
    log_dir = os.path.join(Config.DATA_DIRECTORY, "log")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create/clean log file.
    file_name = "{0}_{1}.log".format(logger_name, get_current_date())
    log_file = os.path.join(log_dir, file_name)
    if os.path.exists(log_file):
        os.remove(log_file)

    # Set log level.
    log_level = getattr(logging, Config.LOG_LEVEL, None)
    if not isinstance(log_level, int):
        raise ValueError('Invalid log level: "{}"'.format(Config.LOG_LEVEL))

    # Configure logger.
    logging.basicConfig(
        filename=log_file,
        format="%(levelname)s %(asctime)s - %(message)s",
        level=log_level,
    )

    # Silence `requests` and `stem` modules logging.
    requests_log = logging.getLogger("requests")
    requests_log.setLevel(logging.WARNING)
    requests.packages.urllib3.disable_warnings()

    stem_log = logging.getLogger("stem")
    stem_log.setLevel(logging.WARNING)
