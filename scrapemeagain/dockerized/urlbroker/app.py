import os

from flask import jsonify

from config import Config
from scrapemeagain.dockerized.utils import app_factory, get_class_from_path


SCRAPER_PACKAGE = os.environ.get('SCRAPER_PACKAGE')


list_urlbroker_class_path = (
    'scrapemeagain.scrapers.{package}.scraper.ListUrlsBroker'.format(
        package=SCRAPER_PACKAGE
    )
)
list_urlbroker_class = get_class_from_path(list_urlbroker_class_path)
LIST_URLBROKER = list_urlbroker_class()

item_urlbroker_class_path = (
    'scrapemeagain.scrapers.{package}.databaser.ItemUrlsBroker'.format(
        package=SCRAPER_PACKAGE
    )
)
item_urlbroker_class = get_class_from_path(item_urlbroker_class_path)
ITEM_URLBROKER = item_urlbroker_class()


app = app_factory(__name__)


def _urls_range_json(start, end):
    return jsonify({
        'start': start,
        'end': end
    })


@app.route('/list-urls-range/')
def list_urls_range():
    start, end = LIST_URLBROKER.get_urls_range()
    return _urls_range_json(start, end)


@app.route('/item-urls-range/')
def item_urls_range():
    start, end = ITEM_URLBROKER.get_urls_range()
    return _urls_range_json(start, end)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=Config.URLBROKER_PORT)
