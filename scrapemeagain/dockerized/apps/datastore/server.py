from flask import request

from scrapemeagain.config import Config
from scrapemeagain.dockerized.utils import app_factory, get_class_from_path


app = app_factory(__name__)


datastore_class = get_class_from_path(Config.DATASTORE_DATABASER_CLASS)
DATASTORE = datastore_class()


@app.route("/insert-data/", methods=["POST"])
def insert_data():
    DATASTORE.insert(request.json)
    return "", 201


@app.route("/commit/")
def commit():
    DATASTORE.commit()
    return "", 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.DATASTORE_PORT)
