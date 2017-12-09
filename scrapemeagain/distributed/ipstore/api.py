import os

from requests import get


IPSTORE_HOST = os.environ.get('IPSTORE_HOST')


def check_ip_safeness(ip):
    """
    Helper to check IP safeness.

    :argument ip: current Tor IP
    :type ip: str

    :returns bool
    """
    url = 'http://{0}:5000/ip-is-safe/{1}/'.format(IPSTORE_HOST, ip)
    return get(url).json()['safe']
