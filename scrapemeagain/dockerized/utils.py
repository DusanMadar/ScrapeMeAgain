import fcntl
import os
from subprocess import CalledProcessError, check_call, PIPE
import socket
import struct
from time import sleep

from flask import Flask

from scrapemeagain.config import Config
from scrapemeagain.utils.logger import setup_logging


def app_factory(name):
    """
    Create a Flask app using scraper specific config. Setup loging and add a
    basic `health` endpoint.

    To be able to use scraper specific config in a module this function has to
    be called first, e.g.

        app = app_factory(__name__)
        urlbroker_class = get_class_from_path(Config.URLBROKER_CLASS)

    :argument name: app name
    :type name: str

    :returns: Flask app
    """
    apply_scraper_config()

    app = Flask(name)

    logger_name = app.root_path.rsplit("/", 1)[-1]
    setup_logging(logger_name)

    @app.route("/health/")
    def healthcheck():
        return ""

    return app


def get_class_from_path(path):
    """
    Get class from given path.

    :argument path: dotted path to the target class
    :type path: str

    :returns: class
    """
    module_path, class_name = path.rsplit(".", 1)
    module = __import__(module_path, fromlist=[class_name])

    return getattr(module, class_name)


def apply_scraper_config(scraper_package=None, scraper_config=None):
    """
    Apply scraper specific config (by simply loading it's module).

    :argument scraper_package: scraper package name
    :type scraper_package: str
    :argument scraper_config: dotted path to scraper config
    :type scraper_config: str

    :returns: class
    """
    if scraper_config is None:
        scraper_config = os.environ.get("SCRAPER_CONFIG")

    if scraper_config is not None:
        get_class_from_path(scraper_config)
        return

    if scraper_package is None:
        scraper_package = os.environ.get("SCRAPER_PACKAGE")

    get_class_from_path("{}.config".format(scraper_package))


def scraper_is_running(hostname):
    """
    Check if a given scraper is running by trying to ping it.

    :argument hostname: scraper's hostname
    :type hostname: str

    :returns: bool
    """
    try:
        result = check_call(
            ["ping", "-c", "2", hostname], stdout=PIPE, stderr=PIPE
        )
    except CalledProcessError:
        result = 1

    # If ping's return code == 0 the scraper is running.
    return result == 0


def wait_for_other_scrapers():
    """
    Wait untill the rest of the scrapers is finished.
    """
    apply_scraper_config()

    for sraper_id in range(0, Config.SCRAPERS_COUNT):
        sraper_id += 1

        if sraper_id == 1:
            continue

        hostname = os.environ.get("SERVICE_NAME_TEMPLATE").format(sraper_id)
        while True:
            if not scraper_is_running(hostname):
                break

            sleep(2)


def get_inf_ip_address(ifname):
    """
    Get IP address of the given interface nameself.

    Credits https://stackoverflow.com/q/24196932/4183498.

    :argument ifname: interface name
    :type ifname: str

    :returns: str
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(
        fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack("256s", bytes(ifname[:15], "utf-8")),
        )[20:24]
    )


def inside_condainer():
    """
    Check if the process runs inside a container.

    Credits: https://stackoverflow.com/q/23513045/4183498.

    :returns: bool
    """
    return os.path.exists("/.dockerenv")
