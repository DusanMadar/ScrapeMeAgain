# -*- coding: utf-8 -*-


"""Setup global logging"""


import os
import logging

import requests

from configparser import get_log_level
from alphanumericker import date_stamp


def setup_logging(logger_name):
    # ensure log directory exists
    parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    log_dir = os.path.join(parent_dir, 'log')

    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    # create/clean log file
    log_name = '{ln}_{ds}.log'.format(ln=logger_name, ds=date_stamp())
    log_file = os.path.join(log_dir, log_name)
    if os.path.exists(log_file):
        os.remove(log_file)

    # get log level
    log_level = get_log_level()
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % log_level)

    # configure global logger
    logging.basicConfig(filename=log_file,
                        level=numeric_level,
                        format='%(levelname)s %(asctime)s - %(message)s')

    # silence `requests` and `stem` modules logging
    requests_log = logging.getLogger('requests')
    requests_log.setLevel(logging.WARNING)
    requests.packages.urllib3.disable_warnings()

    stem_log = logging.getLogger('stem')
    stem_log.setLevel(logging.WARNING)
