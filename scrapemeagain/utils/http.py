import requests

from config import LOCAL_HTTP_PROXY, REQUEST_TIMEOUT


def get(url, **kwargs):
    """GET data from provided URL.

    :argument url:
    :type url: str

    :returns `requests.Response` instance
    """
    kwargs['proxies'] = {
        'http': LOCAL_HTTP_PROXY,
        'https': LOCAL_HTTP_PROXY
    }
    kwargs['verify'] = False
    kwargs['timeout'] = REQUEST_TIMEOUT

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
