import os

from requests import get

from scrapemeagain.config import Config


def _get_urls_range(endpoint):
    """
    Get list URLs range.

    :returns tuple
    """
    url = "http://{host}:{port}/{endpoint}/".format(
        host=os.environ.get("SERVICE_NAME_MASTER_SCRAPER"),
        port=Config.URLBROKER_PORT,
        endpoint=endpoint,
    )
    response_json = get(url).json()

    return (response_json["start"], response_json["end"])


def get_list_urls_range():
    return _get_urls_range("list-urls-range")


def get_item_urls_range():
    return _get_urls_range("item-urls-range")
