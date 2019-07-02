import os

from requests import get, post


BASE_URL = "http://{host}:{port}".format(
    host=os.environ.get("SERVICE_NAME_MASTER_SCRAPER"),
    port=os.environ.get("CONTROLLER_PORT"),
)


def _build_url(endpoint, url_param=None):
    url = "{base}/{endpoint}/".format(base=BASE_URL, endpoint=endpoint)

    if url_param:
        url = "{url}{url_param}/".format(url=url, url_param=url_param)

    return url


def check_ip_safeness(ip):
    url = _build_url("ip-is-safe", ip)
    return get(url).json()["safe"]


def get_list_urls_range():
    url = _build_url("list-urls-range")
    response_json = get(url).json()

    return (response_json["start"], response_json["end"])


def insert_data(data):
    url = _build_url("datastore/insert-data")
    post(url, json=data)


def commit():
    url = _build_url("datastore/commit")
    get(url)
