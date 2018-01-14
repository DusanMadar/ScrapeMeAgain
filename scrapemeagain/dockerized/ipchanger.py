from toripchanger import TorIpChanger

from scrapemeagain.dockerized.ipstore.api import check_ip_safeness


class NetTorIpChanger(TorIpChanger):
    def _ip_is_safe(self, current_ip):
        return check_ip_safeness(current_ip)

    def _manage_used_ips(self, current_ip):
        # No need to maintain used IPs locally the global IP store takes care
        # of that.
        pass
