from requests import get

from scrapemeagain.config import Config


def check_ip_safeness(ip):
    """
    Helper to check IP safeness.

    :argument ip: current Tor IP
    :type ip: str

    :returns bool
    """
    url = "http://{host}:{port}/ip-is-safe/{ip}/".format(
        host=Config.IPSTORE_HOST, port=Config.IPSTORE_PORT, ip=ip
    )
    return get(url).json()["safe"]
