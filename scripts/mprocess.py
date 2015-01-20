#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Multiprocess I/O intensive tasks to maximize performance"""


import time
import logging
import multiprocessing

from databaser import AdsDatabaser
from util.networker import get, ensure_new_ip


def empty_queues(queues):
    """Make sure all used queues are empty

    :argument queues: list of used queues
    :type queues: list (of `multiprocessing.Queue`s)

    """
    for queue in queues:
        items = 0
        while not queue.qsize() == 0:
            queue.get()
            items += 1

        if items != 0:
            logging.warning('%s items removed from %s' % (items, queue))


class AdsFactory():
    def __init__(self, scraper):
        """An implementation of a producer - consumer pattern.

        First of all URL addresses needs to be collected. Catalog URLs can be
        generated as these obey a given pattern. Then catalogs URLs are scraped
        and collected ads URLs are stored the database, from which they are
        sequentially processed using the following procedure.

        Basic idea is to have a pool of producer processes which performs
        HTTP GET requests and feeds the HTML queue (html_q) with lists of
        requests responses.

        Collected responses are processed in another separate process which
        gets the response from HTML queue, scrapes the HTML and pass the
        crunched dictionary data to the DATA queue (data_q).

        The data consumer (yet another separate process) process gets scraped
        data from the DATA queue and store (or whatever) them in the database.

        So the basic pattern is:
        1. get ads URLs
        catalogs URLs -> pool -> html_q -> html_consumer -> db

        2. scrape ads HTML
        db -> pool -> html_q -> html_consumer -> data_q -> data_consumer -> db

        Processes share data using queues, where 'exit' is a signal to stop.
        IP address is changed using TOR after each bunch of requests.

        :argument scraper: scraper instance
        :type scraper: object
        :argument databaser: databaser instance
        :type databaser: object

        """
        self.scraper = scraper

        self.url_q = multiprocessing.Queue()    # strings
        self.html_q = multiprocessing.Queue()   # lists
        self.data_q = multiprocessing.Queue()   # dictionaries

        self.stop_requesting_e = multiprocessing.Event()

        # TODO: process count should be taken from config
        self.pool = multiprocessing.Pool(processes=50)

    def html_producer(self):
        """get URLs from url_q and feed html_q"""
        self.stop_requesting_e.clear()

        while not self.stop_requesting_e.is_set():
            urls = []
            # TODO: process count should be taken from config
            for _ in range(0, 50):
                if self.url_q.empty():
                    break

                urls.append(self.url_q.get())

            if not urls:
                time.sleep(1)
                continue

            ensure_new_ip(used_ips=self.scraper.used_ips)

            try:
                _result = self.pool.map(get, urls)
                self.html_q.put(_result)
            except Exception:
                logging.exception('Can\'t get HTML')
                continue

    def html_consumer(self, scraping):
        """Scrape HTML from the html_q and put collected data to the data_q.
        Consumer process for both catalog and ad pages.

        :argument scraping: indicate if scraping `catalogs` or `ads`
        :type scraping: str

        """
        idle_since = None

        while True:
            # NOTE: tested this as a shared function -> caused high CPU usage
            if self.html_q.qsize() == 0:
                if idle_since is None:
                    idle_since = time.time()
                else:
                    time.sleep(1)
                    now = time.time()

                    if now - idle_since > 30:
                        if not self.stop_requesting_e.is_set():
                            if self.url_q.qsize() == 0:
                                idle_since = None
                                self.stop_requesting_e.set()
                continue

            idle_since = None
            queue_item = self.html_q.get()

            if queue_item == 'exit':
                break

            for response in queue_item:
                if not response.ok:
                    if response.status_code >= 408:
                        self.url_q.put(response.url)
                        continue

                try:
                    if scraping == 'ads':
                        # TODO: get_ad_properties should be renamed
                        # TODO: this can work for other things as well
                        data = self.scraper.get_ad_properties(response)
                    elif scraping == 'catalogs':
                        data = self.scraper.get_catalog_ads(response)

                    self.data_q.put(data)
                except Exception:
                    msg = 'Can\'t scrape %s: %s' % (scraping, response.url)
                    logging.exception(msg)
                    continue

    def data_consumer(self):
        """Write scraped data stored in the data_q to the database. Stop
        all processes if the the old data (already stored in the database)
        threshold have been scraped again."""
        databaser = AdsDatabaser(self.scraper.db_file, self.scraper.db_table)
        # TODO: again, rename, not only ads can be scraped
        old_ads = 0

        while True:
            if self.data_q.qsize() == 0:
                time.sleep(1)
                continue

            queue_item = self.data_q.get()
            if queue_item == 'exit':
                break

            try:
                # saving URLs
                if isinstance(queue_item, list):
                    databaser.insert_multiple(queue_item, databaser.urls)
                    continue

                # ad not found - remove if was stored during previous scrapes
                if len(queue_item) == 1:
                    if databaser.is_stored(queue_item['ad_id']):
                        databaser.delete(queue_item['ad_id'])
                # new ad
                elif not databaser.is_stored(queue_item['ad_id']):
                    databaser.insert(queue_item)
                else:
                    db_ts = databaser.get_timestamp(queue_item['ad_id'])

                    # updated ad
                    if queue_item['last_update'] > db_ts:
                        databaser.update(data=queue_item)
                    # old ad
                    else:
                        old_ads += 1

                        # TODO: this as well should be taken from config
                        if old_ads > 500:
                            logging.warning('Old adds threshold exceeded')
                            self.stop_requesting_e.set()
                            break

                databaser.delete(queue_item['ad_id'], databaser.urls)
            except Exception:
                # TODO: serialize queue_item otherwise
                logging.exception('Can\'t save data %s' % str(queue_item))
                continue

    def get_ads_urls(self):
        """Generate catalogs URLs and store collected ads URLs in the db"""
        catalog_consumer_p = multiprocessing.Process(target=self.html_consumer,
                                                     args=('catalogs',))
        catalog_consumer_p.daemon = True

        url_consumer_p = multiprocessing.Process(target=self.data_consumer)
        url_consumer_p.daemon = True

        # TODO: start and end should be taken from the parent script
        catalogs = self.scraper.generate_catalog_urls(start=100, end=0)
        for catalog in catalogs:
            self.url_q.put(catalog)

        catalog_consumer_p.start()
        url_consumer_p.start()
        self.html_producer()

        self.html_q.put('exit')
        catalog_consumer_p.join()

        self.data_q.put('exit')
        url_consumer_p.join()

    def get_ads_data(self):
        """Parse ads HTML and store collected data in the database"""
        ad_consumer_p = multiprocessing.Process(target=self.html_consumer,
                                                args=('ads',))
        ad_consumer_p.daemon = True

        data_consumer_p = multiprocessing.Process(target=self.data_consumer)
        data_consumer_p.daemon = True

        databaser = AdsDatabaser(self.scraper.db_file, self.scraper.db_table)
        for add_url in databaser.urls_get_all():
            self.url_q.put(add_url[0])

        ad_consumer_p.start()
        data_consumer_p.start()
        self.html_producer()

        self.html_q.put('exit')
        ad_consumer_p.join()

        self.data_q.put('exit')
        data_consumer_p.join()

        empty_queues([self.url_q, self.html_q, self.data_q])
