from multiprocessing import Event
from time import sleep

from scrapemeagain.pipeline import Pipeline


class ExhaustApiLimitPipeLine(Pipeline):
    def prepare_pipeline(self):
        super().prepare_pipeline()

        # New event to determine when an IP should be changed.
        self.change_ip_now = Event()

        # Set this to the upper limit of requests per second your target API
        # is able to handle from a single IP.
        self.workers_count = 5

    def change_ip(self):
        """
        Override the default `change_ip` behavior.

        Unlike the default `scrapemeagain.pipeline.Pipeline.change_ip`, here we
        want to change the IP address only when the `change_ip_now` event is
        set and not after each bunch of requests.

        This way we can use a single IP address until it's requests limit is
        exhausted.
        """
        if self.change_ip_now.is_set():
            self.change_ip_now.clear()
            super().change_ip()

        # Don't overuse the API - make sure you don't fire more than the
        # allowed number of requests per second.
        sleep(0.2)  # The actual sleep time may be different for you!

    def _classify_response(self, response):
        """
        Override the default `_classify_response` behavior.

        Here we have to decide when an IP should be changed based on the
        response returned from server. In our example we assume an API returns
        JSON and the IP is changed if the status is `QUERY_LIMIT_EXHAUSTED`.
        """
        data = response.json()
        status = data["status"]

        if status == "QUERY_LIMIT_EXHAUSTED":
            if not self.change_ip_now.is_set():
                self.change_ip_now.set()

            # Put the URL back for processing again as we didn't get the
            # response we want.
            self.url_queue.put(response.url)
        else:
            # Note that we send the request URL and the already parsed JSON.
            self.response_queue.put((response.url, data))

    def _scrape_data(self, response):
        """
        Override the default `_scrape_data` behavior.

        :argument response: URL and data
        :type response: tuple

        :returns dict or None
        """
        # A dummy example of response processing.
        url, data = response
        target_data = data.get("target_data")

        if target_data is None:
            return

        # Add URL so it can be removed from DB and not scraped again.
        target_data["url"] = url
        return target_data

    def _store_item_properties(self, data):
        """
        Override the default `_store_item_properties` behavior.

        :argument data: item properties
        :type response: dict or None

        :returns dict or None
        """
        # `scrapemeagain.pipeline.Pipeline._store_item_properties` doesn't
        # handle None so do it here.
        if data is None:
            return

        super()._store_item_properties(data)
