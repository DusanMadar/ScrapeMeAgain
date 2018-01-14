import sys
from time import sleep

from requests import get, RequestException


if __name__ == '__main__':
    host = sys.argv[1]
    port = sys.argv[2]
    url = 'http://{host}:{port}/health/'.format(host=host, port=port)

    i = 0
    while i < 10:
        response = None

        try:
            response = get(url)
        except RequestException:
            pass

        if response and response.status_code == 200:
            break
        else:
            i += 1
            sleep(0.5)

    if i > 10:
        sys.exit('Healthcheck failed.')
