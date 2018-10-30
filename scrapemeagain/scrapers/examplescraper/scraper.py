from bs4 import BeautifulSoup

from scrapemeagain.dockerized.apps.urlbroker import (
    client as urlbroker_client,
    urlbrokers,
)
from scrapemeagain.scrapers.basescraper import BaseScraper
from scrapemeagain.scrapers.examplescraper.model import ExampleDataTable


class ExampleScraper(BaseScraper):
    # TODO the IP below is for my local docker bridge. Add a function which
    # can get it dynamically.
    base_url = "http://172.17.0.1:9090/posts/"
    list_url_template = "?page="

    db_file = "example"
    db_table = ExampleDataTable

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

        catalog_urls = (
            self._format_list_url(i) for i in range(start, stop, -1)
        )

        return catalog_urls


class ListUrlsBroker(urlbrokers.ListUrlsBroker):
    def __init__(self):
        scraper = ExampleScraper()
        super().__init__(scraper)
