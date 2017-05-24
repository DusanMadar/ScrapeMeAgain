from random import sample

import requests

from config import Config


def get(url, **kwargs):
    """GET data from provided URL.

    :argument url:
    :type url: str

    :returns `requests.Response` instance
    """
    kwargs['proxies'] = {
        'http': Config.LOCAL_HTTP_PROXY,
        'https': Config.LOCAL_HTTP_PROXY
    }

    kwargs['verify'] = False
    kwargs['timeout'] = Config.REQUEST_TIMEOUT

    user_agent = sample(Config.USER_AGENTS, 1)[0]
    kwargs['headers'] = {'User-Agent': user_agent}

    try:
        response = requests.get(url, **kwargs)
    except Exception as exc:
        # Don't fail on any exception and setup a fake response instead.
        response = requests.Response()
        response.url = url

        if isinstance(exc, requests.exceptions.Timeout):
            response.status_code = 408
        else:
            response.status_code = 503

    return response
