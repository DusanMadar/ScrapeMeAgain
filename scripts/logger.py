# -*- coding: utf-8 -*-
"""Setup global logging"""


import os
import logging

from util.alphanumericker import date_stamp


def setup_logging(logger_name):
    # ensure log directory exists
    log_dir = os.path.join('..', 'log')
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    # setup/clean log file, configure global logger
    log_name = '{ln}_{ds}.log'.format(ln=logger_name, ds=date_stamp())
    log_file = os.path.join(log_dir, log_name)
    if os.path.exists(log_file):
        os.remove(log_file)

    # TODO: get log level from config
    logging.basicConfig(filename=log_file,
                        level=logging.WARNING,
                        format='%(levelname)s %(asctime)s - %(message)s')

    # silence `requests` and `stem` modules logging
    requests_log = logging.getLogger('requests')
    requests_log.setLevel(logging.WARNING)

    requests_log = logging.getLogger('stem')
    requests_log.setLevel(logging.WARNING)
