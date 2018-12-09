from examplescraper.config import Config

# `examplesite` runs locally so we cannot route traffic via privoxy and tor.
Config.LOCAL_HTTP_PROXY = ""

# Don't actualy change tor's IP address.
Config.TORIPCHANGER_CLASS = (
    "tests.integration.fake_ipchanger.FakeDockerizedTorIpChanger"
)

Config.DATA_DIRECTORY = "/tmp/test-examplescraper"
