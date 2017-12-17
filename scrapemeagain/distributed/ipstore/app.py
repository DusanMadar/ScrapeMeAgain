import os

from flask import Flask, jsonify

from toripchanger import TorIpChanger


app = Flask(__name__)


scrapers = int(os.environ.get('SCRAPERS_COUNT'))
scraper_scrape_processes = int(os.environ.get('SCRAPER_SCRAPE_PROCESSES'))
IPSTORE_REUSE_THRESHOLD = scrapers * scraper_scrape_processes
IPSTORE_PORT = int(os.environ.get('IPSTORE_PORT'))
# Global IP store (using only specific `TorIpChanger` functionality).
IPSTORE = TorIpChanger(reuse_threshold=IPSTORE_REUSE_THRESHOLD)


@app.route('/ip-is-safe/<ip>/')
def ip_is_safe(ip):
    safe = IPSTORE._ip_is_safe(ip)
    if safe:
        IPSTORE._manage_used_ips(ip)

    return jsonify({
        'safe': safe
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=IPSTORE_PORT)
