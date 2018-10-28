from scrapemeagain.config import Config
from scrapemeagain.dockerized.apps.utils import app_factory


app = app_factory(__name__)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.HEALTHCHECK_PORT)
