from requests import get

from scrapemeagain.distributed.config import Config


IPSTORE_PORT = Config.IPSTORE_PORT
IPSTORE_HOST = Config.IPSTORE_HOST


def check_ip_safeness(ip):
    """
    Helper to check IP safeness.

    :argument ip: current Tor IP
    :type ip: str

    :returns bool
    """
    url = f'http://{IPSTORE_HOST}:{IPSTORE_PORT}/ip-is-safe/{ip}/'
    return get(url).json()['safe']
