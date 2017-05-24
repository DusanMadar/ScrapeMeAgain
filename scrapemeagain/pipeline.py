"""Multiprocess I/O intensive tasks to maximize performance."""


import logging
from multiprocessing import Event, Pool, Process, Queue
import time

from config import Config
from .utils.http import get


EXIT = '__exit__'


class Pipeline(object):
    def __init__(self, scraper, databaser, tor_ip_changer):
        """Webscraping pipeline.

        How it works:
        1. generate URLs for item list pages
        2. scrape item URLs from list pages
        3. store scraped item URLs in the DB
        4. load item URLs from the DB
        5. collect item properties
        6. store collected data in the DB

        :argument scraper: a scraper instance
        :type scraper: object
        :argument databaser: a databaser instance
        :type databaser: object
        :argument tor_ip_changer: a TorIpChanger instance
        :type tor_ip_changer: object
        """
        self.scraper = scraper
        self.databaser = databaser
        self.tor_ip_changer = tor_ip_changer

        self.scrape_processes = Config.SCRAPE_PROCESSES

        self.transaction_items = 0
        self.transaction_items_max = Config.TRANSACTION_SIZE

        self.workers = []

    def prepare_multiprocessing(self):
        """Prepare all necessary multiprocessing objects."""
        self.url_queue = Queue()
        self.response_queue = Queue()
        self.data_queue = Queue()

        self.pool = Pool(self.scrape_processes)

        self.requesting_in_progress = Event()
        self.scraping_in_progress = Event()

    def change_ip(self):
        """Change IP address.

        By default, IP is chnaged after each bunch of URLs is requested.
        """
        try:
            new_ip = self.tor_ip_changer.get_new_ip()
            logging.info('New IP: {new_ip}'.format(new_ip=new_ip))
        except:
            logging.error('Failed setting new IP')
            self.change_ip()

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
        except:
            logging.error('Failed scraping URLs')
        finally:
            self.requesting_in_progress.clear()

    def get_html(self):
        """Get HTML for URLs from 'url_queue'."""
        run = True

        while run:
            urls = []

            for _ in range(0, self.scrape_processes):
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
            logging.error(
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
        """Store provided data in the DB."""
        try:
            if isinstance(data, list):
                # Storing item URLs.
                self.databaser.insert_multiple(
                    data, self.databaser.item_urls_table
                )
                # self.scrape_processes == len(data).
                self.transaction_items += self.scrape_processes
            else:
                # Storing item data.
                self.databaser.insert(data, self.databaser.item_data_table)

                # Remove processed item URL.
                self.databaser.delete_url(data['url'])

                # As a new item is inserted and it's URL removed.
                self.transaction_items += 2

            if self.transaction_items > self.transaction_items_max:
                self.databaser.commit()
                self.transaction_items = 0
        except:
            logging.error('Failed storing data')

    def store_data(self):
        """Consume 'data_queue' and store provided data in the DB."""
        while True:
            data = self.data_queue.get()
            if data == EXIT:
                break

            self._actually_store_data(data)

        self.databaser.commit()

    def exit_workers(self):
        """Exit workers started as separate processes by passing an EXIT
        message to all queues. This action leads to exiting `while` loops which
        workers processes run in.
        """
        self.url_queue.put(EXIT)
        self.response_queue.put(EXIT)
        self.data_queue.put(EXIT)

    def switch_power(self):
        """Check when to exit processes so the program won't run forever."""
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

    def employ_worker(self, target):
        """Create and register a daemon worker process.

        :argument target: worker's task
        :type target: function
        """
        worker = Process(target=target)
        worker.daemon = True
        worker.start()

        self.workers.append(worker)

    def release_workers(self):
        """Wait till all worker daemons are finished."""
        for worker in self.workers:
            worker.join()

    def get_item_urls(self):
        """Get item URLs from item list pages."""
        # scraper --> url_queue.
        self.employ_worker(self.produce_list_urls)

        # response_queue --> data_queue.
        self.employ_worker(self.collect_data)

        # data_queue --> DB.
        self.employ_worker(self.store_data)

        # Prevent running forever.
        self.employ_worker(self.switch_power)

        # NOTE Execution will block until 'get_html' is finished.
        # url_queue --> response_queue.
        self.get_html()

        self.release_workers()

    def get_item_properties(self):
        """Get item properties from item pages."""
        # DB --> url_queue.
        self.employ_worker(self.produce_item_urls)

        # response_queue --> data_queue.
        self.employ_worker(self.collect_data)

        # data_queue --> DB.
        self.employ_worker(self.store_data)

        # Prevent running forever.
        self.employ_worker(self.switch_power)

        # NOTE Execution will block until 'get_html' is finished.
        # url_queue --> response_queue.
        self.get_html()

        self.release_workers()
