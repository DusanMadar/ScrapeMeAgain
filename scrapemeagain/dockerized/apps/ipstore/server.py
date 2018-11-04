from flask import jsonify
from toripchanger import TorIpChanger

from scrapemeagain.config import Config
from scrapemeagain.dockerized.utils import app_factory


app = app_factory(__name__)


# Global IP store (using only specific `TorIpChanger` functionality).
IPSTORE = TorIpChanger(reuse_threshold=Config.IPSTORE_REUSE_THRESHOLD)


@app.route("/ip-is-safe/<ip>/")
def ip_is_safe(ip):
    safe = IPSTORE._ip_is_safe(ip)
    if safe:
        IPSTORE._manage_used_ips(ip)

    return jsonify({"safe": safe})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.IPSTORE_PORT)
