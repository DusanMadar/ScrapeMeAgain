# -*- coding: utf-8 -*-


"""Read and parse configuration file"""


import os

from sys import exit
from ConfigParser import SafeConfigParser


#: config sections
TOR_SECTION = 'TOR'
DATA_SECTION = 'DATA'
LOGGING_SECTION = 'LOGGING'
GEOCODING_SECTION = 'GEOCODING'
MULTIPROCESSING_SECTION = 'MULTIPROCESSING'


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
    port_option = 'port'
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
    password_option = 'password'
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
    datadir_option = 'directory'
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


def get_old_items_threshold():
    """Get old items threshold

    :returns int

    """
    old_items_option = 'old_items_threshold'
    has_option(DATA_SECTION, old_items_option)

    try:
        return parser.getint(DATA_SECTION, old_items_option)
    except ValueError:
        print 'Old items threshold is either missing or is not an integer'
        exit()


def get_log_level():
    """Get root logger log level

    :returns str

    """
    loglevel_option = 'level'
    has_option(LOGGING_SECTION, loglevel_option)

    log_level = parser.get(LOGGING_SECTION, loglevel_option)
    if not log_level:
        print 'Log level is not specified'
        exit()

    log_levels = ('critical', 'error', 'warning', 'info', 'debug')
    if log_level not in log_levels:
        print 'Invalid log level: %s' % log_level
        print 'Choose one of: %s' % ', '.join(log_levels)
        exit()

    return log_level


def get_geocoding_language():
    """Get geocoding language

    :returns str

    """
    language_option = 'language_code'
    has_option(GEOCODING_SECTION, language_option)

    geocoding_language = parser.get(GEOCODING_SECTION, language_option)
    if not geocoding_language:
        print 'Geocoding language is not specified'
        exit()

    return geocoding_language


def get_ungeocoded_coordinate():
    """Get ungeocoded coordinate

    :returns int

    """
    ungeocoded_option = 'ungeocoded_coordinate'
    has_option(GEOCODING_SECTION, ungeocoded_option)

    try:
        return parser.getint(GEOCODING_SECTION, ungeocoded_option)
    except ValueError:
        print 'Ungeocoded coordinate is either missing or is not an integer'
        exit()


def get_ungeocoded_component():
    """Get ungeocoded component

    :returns str

    """
    ungeocoded_option = 'ungeocoded_component'
    has_option(GEOCODING_SECTION, ungeocoded_option)

    ungeocoded_component = parser.get(GEOCODING_SECTION, ungeocoded_option)
    if not ungeocoded_component:
        print 'Ungeocoded component is not specified'
        exit()

    return ungeocoded_component


def get_scrape_processes():
    """Get number of separate scrape processes

    :returns int

    """
    scrape_processes_option = 'scrape_processes'
    has_option(MULTIPROCESSING_SECTION, scrape_processes_option)

    try:
        return parser.getint(MULTIPROCESSING_SECTION, scrape_processes_option)
    except ValueError:
        print 'Scrape processes count is either missing or is not an integer'
        exit()


def get_geocoding_processes():
    """Get number of separate geocoding processes

    :returns int

    """
    geocoding_processes_option = 'geocoding_processes'
    has_option(MULTIPROCESSING_SECTION, geocoding_processes_option)

    try:
        return parser.getint(MULTIPROCESSING_SECTION,
                             geocoding_processes_option)
    except ValueError:
        print 'Geocoding processes count is either missing or is not an integer'  # NOQA
        exit()


def get_used_ips():
    """Get number of used IPS to remember

    :returns int

    """
    used_ips_option = 'used_ips'
    has_option(MULTIPROCESSING_SECTION, used_ips_option)

    try:
        return parser.getint(MULTIPROCESSING_SECTION, used_ips_option)
    except ValueError:
        print 'Used IPs buffer isze is either missing or is not an integer'
        exit()
