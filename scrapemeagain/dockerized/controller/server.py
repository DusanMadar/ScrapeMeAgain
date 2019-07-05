import flask
from toripchanger import TorIpChanger

from scrapemeagain.config import Config
from scrapemeagain.dockerized.utils import (
    apply_scraper_config,
    get_class_from_path,
)
from scrapemeagain.utils.logger import setup_logging


setup_logging(__name__)
apply_scraper_config()


datastore_class = get_class_from_path(Config.DATASTORE_DATABASER_CLASS)
DATASTORE = datastore_class()
urlbroker_class = get_class_from_path(Config.URLBROKER_CLASS)
URLBROKER = urlbroker_class()
IPSTORE = TorIpChanger(reuse_threshold=Config.IPSTORE_REUSE_THRESHOLD)


app = flask.Flask(__name__)


@app.route("/health/")
def healthcheck():
    return ""


@app.route("/ip-is-safe/<ip>/")
def ip_is_safe(ip):
    safe = IPSTORE._ip_is_safe(ip)
    if safe:
        IPSTORE._manage_used_ips(ip)

    return flask.jsonify({"safe": safe})


@app.route("/list-urls-range/")
def list_urls_range():
    start, end = URLBROKER.get_urls_range()
    return flask.jsonify({"start": start, "end": end})


@app.route("/datastore/insert-data/", methods=["POST"])
def insert_data():
    DATASTORE.insert(flask.request.json)
    return "", 201


@app.route("/datastore/commit/")
def commit():
    DATASTORE.commit()
    return "", 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.CONTROLLER_PORT)
