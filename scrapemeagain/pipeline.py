"""Multiprocess I/O intensive tasks to maximize performance."""


import logging
from multiprocessing import Event, Pool, Process, Queue, Value
import time

from scrapemeagain.config import Config
from scrapemeagain.utils.alnum import get_current_datetime
from scrapemeagain.utils.http import get


EXIT = "__exit__"
DUMP_URLS_BUCKET = "__dump_urls_bucket__"


class Pipeline:
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

        self.workers = []

    def prepare_multiprocessing(self):
        """Prepare all necessary multiprocessing objects."""
        self.url_queue = Queue()
        self.response_queue = Queue()
        self.data_queue = Queue()

        self.pool = Pool(self.scrape_processes)

        self.producing_urls_in_progress = Event()
        self.requesting_in_progress = Event()
        self.scraping_in_progress = Event()

        self.urls_to_process = Value("i", 0)
        self.urls_processed = Value("i", 0)
        self.urls_bucket_empty = Value("i", 1)

    def inform(self, message, log=True, end="\n"):
        """Print and if set log a message.

        :argument message:
        :type message: str
        :argument log: flag to also log the message
        :type log: bool
        :argument end: message line end
        :type end: str
        """
        if log:
            logging.info(message)

        print("{0} {1}".format(get_current_datetime(), message), end=end)

    def _inform_progress(self):
        """Print a message about how the scraping is progressing."""
        try:
            message = "Processed {0} ({1:.2f}%) URLs".format(
                self.urls_processed.value,
                self.urls_processed.value / self.urls_to_process.value * 100,
            )
            self.inform(message, log=False, end="\r")
        except ZeroDivisionError:
            pass

    def change_ip(self):
        """Change IP address.

        By default, IP is changed after each bunch of URLs is requested.
        """
        try:
            new_ip = self.tor_ip_changer.get_new_ip()
            logging.info("New IP: {new_ip}".format(new_ip=new_ip))
        except:
            logging.error("Failed setting new IP")
            return self.change_ip()

    def _produce_urls_wrapper(self, producer_function):
        """Use the provided 'producer_function' to populate 'url_queue'
        and get URLs count.

        :argument producer_function: how to produce URLs
        :type producer_function: function/method
        """
        self.producing_urls_in_progress.set()

        urls_count = producer_function()

        self.inform("URLs to process: {}".format(urls_count))
        time.sleep(1)
        self.urls_to_process.value = urls_count

        self.producing_urls_in_progress.clear()

    def _actually_produce_list_urls(self):
        return self.scraper.generate_list_urls()

    def produce_list_urls(self):
        """Populate 'url_queue' with generated list URLs."""

        def producer_function():
            urls_count = 0
            for list_url in self._actually_produce_list_urls():
                self.url_queue.put(list_url)
                urls_count += 1

            return urls_count

        self._produce_urls_wrapper(producer_function)

    def _actually_produce_item_urls(self):
        return self.databaser.get_item_urls()

    def produce_item_urls(self):
        """Populate 'url_queue' with loaded item URLs."""

        def producer_function():
            urls_count = 0
            for item_url in self._actually_produce_item_urls():
                # Pick the URL from SQLAlchemy ResultProxy.
                self.url_queue.put(item_url[0])
                urls_count += 1

            return urls_count

        self._produce_urls_wrapper(producer_function)

    def _classify_response(self, response):
        """Examine response and put it to 'response_queue' if it's OK or put
        it's URL  back to 'url_queue'.

        :argument response:
        :type response: request.response
        """
        if not response.ok and response.status_code >= 408:
            self.url_queue.put(response.url)
        else:
            self.response_queue.put(response)

    def _actually_get_html(self, urls):
        """Request provided URLs running multiple processes.

        :argument urls: URLs to get data from
        :type urls: list
        """
        try:
            self.requesting_in_progress.set()
            for response in self.pool.map(get, urls):
                self._classify_response(response)
        except Exception as exc:
            logging.error("Failed scraping URLs")
            logging.exception(exc)
        finally:
            self.requesting_in_progress.clear()

    def get_html(self):
        """Get HTML for URLs from 'url_queue'."""
        run = True

        while run:
            urls_bucket = []
            self.urls_bucket_empty.value = 1
            for _ in range(0, self.scrape_processes):
                url = self.url_queue.get()

                if url == EXIT:
                    run = False
                    break
                elif url == DUMP_URLS_BUCKET:
                    break

                urls_bucket.append(url)
                if self.urls_bucket_empty.value:
                    self.urls_bucket_empty.value = 0

            if urls_bucket:
                self._actually_get_html(urls_bucket)

            if run:
                self.change_ip()

    def _scrape_data(self, response):
        """Scrape HTML provided by the given response.

        :argument response:
        :type response: request.response

        :returns dict
        """
        if self.scraper.list_url_template in response.url:
            data = self.scraper.get_item_urls(response)
        else:
            data = self.scraper.get_item_properties(response)

        return data

    def _actually_collect_data(self, response):
        """Collect data from the given response.

        :argument response:
        :type response: request.response
        """
        try:
            self.scraping_in_progress.set()

            data = self._scrape_data(response)
            if data:
                self.data_queue.put(data)
        except Exception as exc:
            logging.error(
                'Failed processing response for "{}"'.format(response.url)
            )
            logging.exception(exc)
        finally:
            self.scraping_in_progress.clear()

    def collect_data(self):
        """Get data for responses from 'response_queue'."""
        while True:
            response = self.response_queue.get()

            if response == EXIT:
                break

            self._actually_collect_data(response)

    def _store_item_urls(self, data):
        """Handle storing item URLs.

        :argument data: item URLs
        :type data: list
        """
        if not data:
            return

        self.databaser.insert_multiple(data, self.databaser.item_urls_table)

    def _store_item_properties(self, data):
        """Handle storing item properties.

        :argument data: item properties
        :type data: dict
        """
        if len(data) > 1:
            # NOTE: if there is only a single item in the data dict (the URL),
            # there is no point in storing it.
            self.databaser.insert(data, self.databaser.item_data_table)

        # Remove processed item URL.
        self.databaser.delete_url(data["url"])

    def _actually_store_data(self, data):
        """Store provided data in the DB.

        :argument data: data to store in the DB
        :type data: str or list or dict
        """
        try:
            if isinstance(data, list):
                self._store_item_urls(data)
            else:
                self._store_item_properties(data)
        except Exception as exc:
            logging.error("Failed storing data")
            logging.exception(exc)
        finally:
            self.urls_processed.value += 1

    def store_data(self):
        """Consume 'data_queue' and store provided data in the DB."""
        self.urls_processed.value = 0

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
        self.inform("Exiting workers, please wait ...")

        self.url_queue.put(EXIT)
        self.response_queue.put(EXIT)
        self.data_queue.put(EXIT)

    def _queues_empty(self):
        """Check if queues are empty.

        :returns bool
        """
        return (
            self.url_queue.empty()
            and self.response_queue.empty()
            and self.data_queue.empty()
        )

    def _workers_idle(self):
        """Check if workers are idle.

        :returns bool
        """
        return (
            not self.producing_urls_in_progress.is_set()
            and not self.requesting_in_progress.is_set()
            and not self.scraping_in_progress.is_set()
        )

    def switch_power(self):
        """Check when to exit workers so the program won't run forever."""
        while True:
            # Check if workers can end.
            if (
                self._queues_empty()
                and self._workers_idle()
                and self.urls_bucket_empty.value
            ):
                self.exit_workers()
                break

            # Ensure all URLs are processed.
            if (
                self._queues_empty()
                and self._workers_idle()
                and not self.urls_bucket_empty.value
            ):
                logging.info("Dumping URLs bucket")
                self.url_queue.put(DUMP_URLS_BUCKET)

            # Inform about the progress.
            self._inform_progress()
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
        self.inform("Collecting item URLs")

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
        self.inform("Collecting item properties")

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


class DockerizedPipeline(Pipeline):
    def inform(self, message, log=True, **kwargs):
        # Prevent using `end = '\r'` as that way docker-compose won't show all
        # messages.
        super().inform(message, log=log, end="\n")
