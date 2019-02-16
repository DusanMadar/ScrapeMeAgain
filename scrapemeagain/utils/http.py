"""Common HTTP functions."""


import asyncio
from collections import namedtuple
import logging
from random import sample

import aiohttp

from scrapemeagain.config import Config


HTTP_PROXY = f"http://{Config.LOCAL_HTTP_PROXY}"
RESPONSE_LOG_MESSAGE = "{status} - {url}"

Response = namedtuple("Response", "url status data")


def setup_aiohttp_client():
    connector = aiohttp.TCPConnector(force_close=True, ssl=False)
    timeout = aiohttp.ClientTimeout(total=Config.REQUEST_TIMEOUT)
    return aiohttp.ClientSession(connector=connector, timeout=timeout)


async def aget(url, client, **kwargs):
    """Asynchronously GET data from provided URL.

    :argument url:
    :type url: str

    :returns `Response` instance
    """
    kwargs["proxy"] = HTTP_PROXY
    kwargs["headers"] = {"User-Agent": sample(Config.USER_AGENTS, 1)[0]}

    try:
        async with client.get(url, **kwargs) as aresp:
            data = await aresp.text()

        logging.debug(
            RESPONSE_LOG_MESSAGE.format(status=aresp.status, url=url)
        )

        if url != str(aresp.url):
            logging.warning("Requested {0} got {1}".format(url, aresp.url))

        status = aresp.status
    except Exception as exc:
        # Don't fail on any exception and setup a fake response instead.
        if isinstance(exc, asyncio.TimeoutError):
            status = 408
        else:
            status = 503

        error_message = RESPONSE_LOG_MESSAGE.format(status=status, url=url)

        try:
            error_message += " - {}".format(str(exc))
        finally:
            logging.error(error_message)

        data = None

    response = Response(url, status, data)
    return response
