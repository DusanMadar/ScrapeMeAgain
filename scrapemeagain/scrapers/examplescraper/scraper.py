import os

from bs4 import BeautifulSoup

from scrapemeagain.dockerized.apps.urlbroker import (
    client as urlbroker_client,
    urlbrokers,
)
from scrapemeagain.dockerized.utils import inside_condainer
from scrapemeagain.scrapers.basescraper import BaseScraper
from scrapemeagain.scrapers.examplescraper.model import ExampleDataTable


class ExampleScraper(BaseScraper):
    base_url = "http://localhost:9090/posts/"
    list_url_template = "?page="

    db_file = "example"
    db_table = ExampleDataTable

    def __init__(self):
        # NOTE you don't need to do this for publicly accessible websites. In
        # fact, the whole __init__ method is here "only" to enable testing with
        # Docker. Containers cannot access host's localhost and hence we have
        # to point the scraper to `DOCKER_HOST_IP` (and examplesite has to be
        # running on that same address of course).
        if inside_condainer():
            self.base_url = self.base_url.replace(
                "localhost", os.environ.get("DOCKER_HOST_IP")
            )

    def _format_list_url(self, index):
        return self.base_url + self.list_url_template + str(index)

    def generate_list_urls(self):
        list_count = self.get_lists_count()

        return (self._format_list_url(i) for i in range(0, list_count, 10))

    def get_lists_count(self):
        # We only want first 10 lists.
        return 110

    def get_item_urls(self, response):
        links = []
        soup = BeautifulSoup(response.content, "html.parser")

        for h3 in soup.findAll("h3"):
            url_data = {"url": h3.find("a").get("href")}

            links.append(url_data)

        return links

    def get_item_properties(self, response):
        # TODO how about moveing this to '_actually_collect_data()'?
        # Always provide an URL so it can be removed from URLs table
        # (and thus marked as processed).
        properties = {"url": response.url}

        soup = BeautifulSoup(response.content, "html.parser")

        headers = soup.findAll("h1")
        if headers:
            properties["h1"] = headers[0].text

        return properties


class DockerizedExampleScraper(ExampleScraper):
    def generate_list_urls(self):
        start, stop = urlbroker_client.get_list_urls_range()
        return (self._format_list_url(i) for i in range(start, stop, -1))


class ListUrlsBroker(urlbrokers.ListUrlsBroker):
    def __init__(self):
        scraper = ExampleScraper()
        super().__init__(scraper)
