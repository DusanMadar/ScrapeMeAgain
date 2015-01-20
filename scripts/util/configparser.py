#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Read and parse configuration file"""

import os

from sys import exit
from ConfigParser import SafeConfigParser


#: config sections
TOR_SECTION = 'TOR'
DATA_SECTION = 'DATA'
LOGGING_SECTION = 'LOGGING'


parent_dir = os.sep.join([part for part in __file__.split(os.sep)[:-3]])
config_file = os.path.join(parent_dir, 'config.ini')
if not os.path.exists(config_file):
    print 'Can\'t find file `config.ini` in %s.' % parent_dir
    exit()


parser = SafeConfigParser()
parser.read(config_file)


def has_section(section):
    """Check if section is present in the config file

    :argument section: section name
    :type section: str

    :returns bool

    """
    if not parser.has_section(section):
        print 'Can\'t find section `%s` in %s' % (section, config_file)
        print 'NOTE: section names are case sensitive'
        exit()

    return True


def has_option(section, option):
    """Check if option is present under section in the config file

    :argument section: section name
    :type section: str
    :argument option: option name
    :type option: str

    :returns bool

    """
    has_section(section)

    if not parser.has_option(section, option):
        print ('Can\'t find option `%s` under section `%s` in %s' %
               (option, section, config_file))
        exit()

    return True


def get_tor_port():
    """Get TOR port number

    :returns int

    """
    port_option = 'Port'
    has_option(TOR_SECTION, port_option)

    try:
        return parser.getint(TOR_SECTION, port_option)
    except ValueError:
        print 'TOR port number is either missing or is not an integer'
        exit()


def get_tor_password():
    """Get TOR password

    :returns str

    """
    password_option = 'Password'
    has_option(TOR_SECTION, password_option)

    tor_password = parser.get(TOR_SECTION, password_option)
    if not tor_password:
        print 'TOR password is not specified'
        exit()

    return tor_password


def get_data_directory():
    """Get data directory

    :returns str

    """
    datadir_option = 'Directory'
    has_option(DATA_SECTION, datadir_option)

    data_directory = parser.get(DATA_SECTION, datadir_option)
    if not data_directory:
        print 'Data directory is not specified'
        exit()

    if not os.path.exists(data_directory):
        print 'Directory `%s` does not exists' % data_directory
        exit()

    if not os.path.isdir(data_directory):
        print '`%s` is not a directory' % data_directory
        exit()

    return data_directory


def get_log_level():
    """Get root logger log level

    :returns str

    """
    loglevel_option = 'Logging'
    has_option(LOGGING_SECTION, loglevel_option)

    log_level = parser.get(LOGGING_SECTION, loglevel_option)
    if not log_level:
        print 'Log level is not specified'
        exit()

    return log_level
