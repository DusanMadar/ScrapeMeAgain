"""Common HTTP functions."""


import logging
from random import sample

import requests

from scrapemeagain.config import Config


RESPONSE_LOG_MESSAGE = "{status} - {url}"


def get(url, **kwargs):
    """GET data from provided URL.

    :argument url:
    :type url: str

    :returns `requests.Response` instance
    """
    kwargs["proxies"] = {
        "http": Config.LOCAL_HTTP_PROXY,
        "https": Config.LOCAL_HTTP_PROXY,
    }

    kwargs["verify"] = False
    kwargs["timeout"] = Config.REQUEST_TIMEOUT

    user_agent = sample(Config.USER_AGENTS, 1)[0]
    kwargs["headers"] = {"User-Agent": user_agent}

    try:
        response = requests.get(url, **kwargs)

        logging.debug(
            RESPONSE_LOG_MESSAGE.format(status=response.status_code, url=url)
        )

        # NOTE: set the actually requested URL (as that one is stored in the
        # item_urls DB table).
        if url != response.url:
            logging.warning("Requested {0} got {1}".format(url, response.url))
            response.url = url
    except Exception as exc:
        # Don't fail on any exception and setup a fake response instead.
        response = requests.Response()
        response.url = url

        if isinstance(exc, requests.exceptions.Timeout):
            response.status_code = 408
        else:
            response.status_code = 503

        error_message = RESPONSE_LOG_MESSAGE.format(
            status=response.status_code, url=url
        )

        try:
            error_message += " - {}".format(str(exc))
        finally:
            logging.error(error_message)

    return response
