from flask import Flask, jsonify

from scrapemeagain.distributed.config import Config
from scrapemeagain.distributed.utils import get_class_from_path


scraper_class = get_class_from_path(Config.CONTROLLER_CLASS)
SCRAPER = scraper_class()


app = Flask(__name__)


@app.route('/list-urls-range/')
def list_urls_range():
    start, end = SCRAPER.get_list_urls_range()

    return jsonify({
        'start': start,
        'end': end
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=Config.CONTROLLER_PORT)
