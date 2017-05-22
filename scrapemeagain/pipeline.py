"""Multiprocess I/O intensive tasks to maximize performance."""


import logging
from multiprocessing import Event, Pool, Process, Queue
import time

import config
from toripchanger import TorIpChanger
from .utils.http import get


EXIT = '__exit__'


class Pipeline(object):
    def __init__(self, scraper, databaser):
        """

        :argument scraper: a scraper instance
        :type scraper: object
        :argument databaser: a databaser instance
        :type databaser: object
        """
        self.scraper = scraper
        self.databaser = databaser

    def prepare_multiprocessing(self):
        self.processes = config.SCRAPE_PROCESSES

        self.url_queue = Queue()
        self.response_queue = Queue()
        self.data_queue = Queue()

        self.pool = Pool(processes=self.processes)

        self.requesting_in_progress = Event()
        self.scraping_in_progress = Event()

    def prepare_dependencies(self):
        self.tor_ip_changer = TorIpChanger(
            reuse_threshold=config.REUSE_THRESHOLD,
            local_http_proxy=config.LOCAL_HTTP_PROXY,
            tor_password=config.TOR_PASSWORD,
            tor_port=config.TOR_PORT,
            new_ip_max_attempts=config.NEW_IP_MAX_ATTEMPTS
        )

    def change_ip(self):
        """Change IP address.

        By default, IP is chnaged after each bunch of URLs is requested.
        """
        self.tor_ip_changer.get_new_ip()

    def produce_list_urls(self):
        """Populate 'url_queue' with generated list URLs."""
        for list_url in self.scraper.generate_list_urls():
            self.url_queue.put(list_url)

    def produce_item_urls(self):
        """Populate 'url_queue' with loaded item URLs."""
        for item_url in self.databaser.get_item_urls():
            self.url_queue.put(item_url)

    def _classify_response(self, response):
        """Examine response and put it to 'response_queue' if it's OK or put
        it's URL  back to 'url_queue'.
        """
        print(response)
        if not response.ok and response.status_code >= 408:
            self.url_queue.put(response.url)
        else:
            self.response_queue.put(response)

    def _actually_get_html(self, urls):
        """Request provided URLs running multiple processes."""
        try:
            self.requesting_in_progress.set()
            for response in self.pool.map(get, urls):
                self._classify_response(response)
        except Exception:
            logging.exception('Failed scraping URLs')
        finally:
            self.requesting_in_progress.clear()

    def get_html(self):
        """Get HTML for URLs from 'url_queue'."""
        run = True

        while run:
            urls = []

            for _ in range(0, self.processes):
                url = self.url_queue.get()

                print(url)
                if url == EXIT:
                    run = False
                    break

                urls.append(url)

            if urls:
                self._actually_get_html(urls)
                self.change_ip()

    def _actually_collect_data(self, response):
        """Scrape HTML provided by a given response."""
        try:
            self.scraping_in_progress.set()
            if self.scraper.list_url_template in response.url:
                data = self.scraper.get_item_urls(response)
            else:
                data = self.scraper.get_item_properties(response)

            self.data_queue.put(data)
        except:
            logging.exception(
                'Failed processing response for "{}"'.format(response.url)
            )
        finally:
            self.scraping_in_progress.clear()

    def collect_data(self):
        """Get data for responses from 'response_queue'."""
        while True:
            response = self.response_queue.get()

            if response == EXIT:
                break

            self._actually_collect_data(response)

    def _actually_store_data(self, data):
        try:
            if isinstance(data, list):
                # Storing item URLs.
                self.databaser.insert_multiple(
                    data, self.databaser.item_urls_table
                )
                self.transaction_items += self.processes
            else:
                # Storing item data.
                self.databaser.insert(data, self.databaser.item_data_table)
                self.transaction_items += 1

                # Remove processed item URL.
                self.databaser.delete_url(data['url'])

            if self.transaction_items > 5000:
                self.databaser.commit()
                self.transaction_items = 0
        except:
            logging.exception('Failed storing data')

    def store_data(self):
        while True:
            data = self.data_queue.get()
            if data == EXIT:
                break

            self._actually_store_data(data)

        self.databaser.commit()
        self.transaction_items = 0

    def exit_workers(self):
        self.url_queue.put(EXIT)
        self.response_queue.put(EXIT)
        self.data_queue.put(EXIT)

    def check_queues(self):
        while True:
            if (
                self.url_queue.empty() and
                self.response_queue.empty() and
                self.data_queue.empty() and
                not self.requesting_in_progress.is_set() and
                not self.scraping_in_progress.is_set()
            ):
                self.exit_workers()
                break
            else:
                time.sleep(5)

    def get_item_urls(self):
        # scraper --> url_queue.
        item_list_urls_producer = Process(target=self.produce_list_urls)
        item_list_urls_producer.daemon = True
        item_list_urls_producer.start()

        # response_queue --> data_queue.
        data_collector = Process(target=self.collect_data)
        data_collector.daemon = True
        data_collector.start()

        # data_queue --> DB.
        data_storer = Process(target=self.store_data)
        data_storer.daemon = True
        data_storer.start()

        # Prevent endless loop.
        queue_checker = Process(target=self.check_queues)
        queue_checker.daemon = True
        queue_checker.start()

        # url_queue --> response_queue.
        self.get_html()
