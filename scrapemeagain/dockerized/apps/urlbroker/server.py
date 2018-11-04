from flask import jsonify

from scrapemeagain.config import Config
from scrapemeagain.dockerized.utils import app_factory, get_class_from_path


app = app_factory(__name__)


urlbroker_class = get_class_from_path(Config.URLBROKER_CLASS)
URLBROKER = urlbroker_class()


@app.route("/list-urls-range/")
def list_urls_range():
    start, end = URLBROKER.get_urls_range()
    return jsonify({"start": start, "end": end})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.URLBROKER_PORT)
