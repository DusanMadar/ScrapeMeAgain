from flask import Flask

from scrapemeagain.utils.logger import setup_logging
from scrapemeagain.dockerized.utils import apply_scraper_config


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

    logger_name = app.root_path.rsplit('/', 1)[-1]
    setup_logging(logger_name)

    @app.route('/health/')
    def healthcheck():
        return ''

    return app
