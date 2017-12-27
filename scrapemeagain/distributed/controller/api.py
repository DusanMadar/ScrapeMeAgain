from requests import get

from scrapemeagain.distributed.config import Config


CONTROLLER_PORT = Config.CONTROLLER_PORT
CONTROLLER_HOST = Config.CONTROLLER_HOST


def get_list_urls_range():
    """
    Get list URLs range.

    :returns tuple
    """
    url = 'http://{host}:{port}/list-urls-range/'.format(
        host=CONTROLLER_HOST, port=CONTROLLER_PORT
    )
    response_json = get(url).json()

    return (response_json['start'], response_json['end'])
