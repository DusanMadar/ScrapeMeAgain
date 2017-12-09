import os

from flask import Flask, jsonify

from toripchanger import TorIpChanger


app = Flask(__name__)


# Global IP store (using only specific `TorIpChanger` functionality).
reuse_threshold = int(os.environ.get('IPSTORE_REUSE_THRESHOLD'))
ipstore = TorIpChanger(reuse_threshold=reuse_threshold)


@app.route('/ip-is-safe/<ip>/')
def ip_is_safe(ip):
    safe = ipstore._ip_is_safe(ip)
    if safe:
        ipstore._manage_used_ips(ip)

    return jsonify({
        'safe': safe
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0')
