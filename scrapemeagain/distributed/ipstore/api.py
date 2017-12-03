from requests import get


# TODO the master scraper (and an IP store at the same time) host (container
# name) should be dynamic (taken from env or something).
IPSTORE_HOST = 'scp1'


def check_ip_safeness(ip):
    """
    Helper to check IP safeness.

    :argument ip: current Tor IP
    :type ip: str

    :returns bool
    """
    url = 'http://{0}:5000/ip-is-safe/{1}/'.format(IPSTORE_HOST, ip)
    return get(url).json()['safe']
