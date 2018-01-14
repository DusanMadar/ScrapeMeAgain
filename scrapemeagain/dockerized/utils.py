from subprocess import CalledProcessError, check_call, PIPE
from time import sleep

from flask import Flask

from config import Config


def app_factory(name):
    """
    Create a Flask app with the basic `health` endpoint.

    :argument name: app name
    :type name: str

    :returns: Flask app
    """
    app = Flask(name)

    @app.route('/health/')
    def healthcheck():
        return ''

    return app


def get_class_from_path(path):
    """
    Get class from given path.

    :argument path: dotted path to the target class
    :type path: str

    :returns: class
    """
    module_path, class_name = path.rsplit('.', 1)
    module = __import__(module_path, fromlist=[class_name])

    return getattr(module, class_name)


def scraper_is_running(hostname):
    """
    Check if a given scraper is running by trying to ping it.

    :argument hostname: scraper's hostname
    :type hostname: str

    :returns: bool
    """
    print('Checking "{}" availability')

    try:
        result = check_call(
            ['ping', '-c', '2', hostname], stdout=PIPE, stderr=PIPE
        )
    except CalledProcessError:
        result = 1

    # It ping's return code == 0 the scraper is running.
    return result == 0


def wait_for_other_scrapers():
    """
    Wait untill the rest of the scrapers is finished.
    """
    for sraper_id in range(0, Config.SCRAPERS_COUNT):
        sraper_id += 1

        if sraper_id == 1:
            continue

        hostname = 'scp{}'.format(sraper_id)
        while True:
            if not scraper_is_running(hostname):
                break

            sleep(2)
