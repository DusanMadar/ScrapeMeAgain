import os

from requests import get


IPSTORE_PORT = os.environ.get('IPSTORE_PORT')
IPSTORE_HOST = os.environ.get('MASTER_SCRAPER')


def check_ip_safeness(ip):
    """
    Helper to check IP safeness.

    :argument ip: current Tor IP
    :type ip: str

    :returns bool
    """
    url = f'http://{IPSTORE_HOST}:{IPSTORE_PORT}/ip-is-safe/{ip}/'
    return get(url).json()['safe']
