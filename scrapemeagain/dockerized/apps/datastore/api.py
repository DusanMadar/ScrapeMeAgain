from requests import get, post

from scrapemeagain.config import Config


def _get_datastore_url(endpoint):
    return "http://{host}:{port}/{endpoint}/".format(
        host=Config.DATASTORE_HOST,
        port=Config.DATASTORE_PORT,
        endpoint=endpoint,
    )


def insert_data(data):
    url = _get_datastore_url("insert-data")
    post(url, json=data)


def commit():
    url = _get_datastore_url("commit")
    get(url)
