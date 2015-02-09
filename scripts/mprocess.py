#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Multiprocess I/O intensive tasks to maximize performance"""


import abc
import time
import logging
import multiprocessing

from geocoder import Geocoder
from databaser import AdsDatabaser, GeoDatabaser
from util.networker import ensure_new_ip, get, get_geo, get_rgeo
from util.configparser import (get_scrape_processes, get_geocoding_processes,
                               get_old_items_threshold)


#: constants
__geo__ = 'geo'
__ads__ = 'ads'
__exit__ = 'exit'
__catalogs__ = 'catalogs'
scrape_processes = get_scrape_processes()
geocoding_processes = get_geocoding_processes()
old_items_threshold = get_old_items_threshold()


class ProducerConsumer(object):
    def __init__(self, scraper, processes):
        """An implementation of a producer - consumer pattern.

        Basic idea is to have a pool of producer processes which performs
        HTTP GET requests and feeds the `responses_q` with lists of requests
        responses. This pool of producer processes is operating upon data from
        the `target_q`, which items can be of various type, depending on what
        kind of data is actually being scraped.

        Collected responses are processed in a separate process which gets the
        response from `responses_q`, processes the data and pass the crunched
        dictionary to the `data_q`.

        The data consumer (yet another separate process) process gets scraped
        data from the `data_q` and store them in the database.

        All abstract methods must be implemented by all successor classes,
        which knows exactly what and how to do.
        Also, `databaser_type` must be set by the all successor classes.

        Stop issuing requests is an event based action.
        Processes share data using queues, where 'exit' is a signal to stop.

        :argument scraper: scraper instance
        :type scraper: `:class:Scraper`
        :argument processes: number of processes to be used
        :type processes: int

        """
        self.scraper = scraper

        self.databaser_type = None
        self.transaction_items = 0

        self.target_q = multiprocessing.Queue()
        self.responses_q = multiprocessing.Queue()
        self.data_q = multiprocessing.Queue()

        self.queues = [('target_q', self.target_q),
                       ('responses_q', self.responses_q),
                       ('data_q', self.data_q)]

        self.stop_requesting_e = multiprocessing.Event()

        self.processes = processes
        self.pool = multiprocessing.Pool(processes=processes)

    @abc.abstractmethod
    def manage_ip(self):
        """Manage IP address manipulation - when to switch it"""
        raise NotImplementedError()

    @abc.abstractmethod
    def collect_data(self, queue_item):
        """Collect data - which and how, put collected data to the `data_q`"""
        raise NotImplementedError()

    @abc.abstractmethod
    def store_data(self, queue_item, databaser):
        """Store data - what checks should be performed and where to save"""
        raise NotImplementedError()

    def create_databaser(self, databaser_type=None):
        """Dispatcher providing appropriate databaser instance

        :argument databaser_type: databaser type
        :type databaser_type: str

        :returns `:class:Databaser`

        """
        if databaser_type is None:
            databaser_type = self.databaser_type

        if databaser_type is None:
            raise ValueError('Databaser type not set')

        elif databaser_type == __ads__:
            dtbsr = AdsDatabaser(self.scraper.db_file, self.scraper.db_table)

        elif databaser_type == __geo__:
            dtbsr = GeoDatabaser()

        else:
            msg = 'Unsupported databaser type "%s"' % self.databaser_type
            raise ValueError(msg)

        return dtbsr

    def commit_checker(self, databaser, queue_item, transaction_size):
        """Commit changes if transaction size is exceeded.
        Large transactions are better for SQLite performance with normal
        synchronization mode (using db-journal), i.e. no need for the
        `pragma synchronous=OFF`, which was used when each change was committed
        separately.

        :argument databaser: databaser instance
        :type databaser: `:class:Databaser`
        :argument queue_item:
        :type queue_item: list or dict
        :argument transaction_size: transaction size
        :type transaction_size: int

        """
        if isinstance(queue_item, list):
            self.transaction_items += len(queue_item)
        else:
            self.transaction_items += 1

        if self.transaction_items >= transaction_size:
            self.transaction_items = 0
            databaser.commit()

    def empty_queues(self):
        """Make sure all queues are empty to prevent endless processes"""
        for qname, queue in self.queues:
            items = 0
            while not queue.qsize() == 0:
                queue.get()
                items += 1

            if items != 0:
                logging.warning('%s items removed from %s' % (items, qname))

    def produce_data(self, requester=None, wait=False):
        """Issue HTTP GET requests, put responses to the `responses_q`

        :argument requester: function used to issue the GET request
        :type requester: function
        :argument wait: flag if wait after issuing requests
        :type wait: bool

        """
        self.stop_requesting_e.clear()

        if requester is None:
            requester = get

        while not self.stop_requesting_e.is_set():
            targets = []

            for _ in range(0, self.processes):
                if self.target_q.empty():
                    break

                targets.append(self.target_q.get())

            if not targets:
                time.sleep(1)
                continue

            self.manage_ip()

            try:
                responses = self.pool.map(requester, targets)
                self.responses_q.put(responses)
            except Exception:
                logging.exception('Failed producing data')
                continue

            if wait:
                time.sleep(0.2)

    def process_data(self):
        """Process responses from `responses_q`. Given implementation of the
        `collect_data` method knows exactly what to do and eventually put
        processed data to the `data_q`."""
        idle_since = None

        while True:
            if self.responses_q.qsize() == 0:
                if idle_since is None:
                    idle_since = time.time()
                else:
                    time.sleep(1)
                    now = time.time()
                    idle_for = now - idle_since

                    if idle_for > 30:
                        if not self.stop_requesting_e.is_set():
                            if self.target_q.qsize() == 0:
                                idle_since = None
                                self.stop_requesting_e.set()

                    # be sure the process is not running forever
                    if idle_for > 120:
                        if not self.stop_requesting_e.is_set():
                            self.stop_requesting_e.set()

                continue

            idle_since = None
            queue_item = self.responses_q.get()

            if queue_item == __exit__:
                break

            self.collect_data(queue_item)

    def consume_data(self):
        """Write processed data from the `data_q` to the database. Given
        implementation of the `store_data` method knows exactly what to do and
        where the data should be stored eventually."""
        databaser = self.create_databaser()

        while True:
            if self.data_q.qsize() == 0:
                time.sleep(1)
                continue

            queue_item = self.data_q.get()
            if queue_item == __exit__:
                break

            try:
                self.store_data(queue_item, databaser)
            except Exception:
                logging.exception('Failed consuming data')
                continue

        if self.transaction_items > 0:
            databaser.commit()


class AdsFactory(ProducerConsumer):
    def __init__(self, scraper):
        """
        First of all all URL addresses needs to be collected. Catalog URLs can
        be generated as these obey a given pattern. Then catalogs URLs are
        scraped and collected ads URLs are stored in the database, from which
        they are sequentially (multi) processed and eventually saved.

        1. get ads URLs
        generate_catalog_urls() -> target_q -> produce_data() -> responses_q ->
        process_data() -> data_q -> store_data() -> scraper database

        2. get ads data
        scraper database -> target_q -> produce_data() -> responses_q ->
        process_data() -> data_q -> store_data() -> scraper database

        IP address is changed after each bunch of requests.

        `scraping` attribute is used to specify what is being scraped, i.e. if
        catalogs or ads.

        `target_q` in this implementation is filled with URLs (catalog or ad).

        :argument scraper: scraper instance
        :type scraper: `:class:Scraper`

        """
        super(AdsFactory, self).__init__(scraper=scraper,
                                         processes=scrape_processes)

        self.scraping = None
        self.old_ads_count = 0
        self.databaser_type = __ads__

    def manage_ip(self):
        """Just set new IP address after each bunch of requests"""
        ensure_new_ip(used_ips=self.scraper.used_ips)

    def collect_data(self, queue_item):
        """Collect and process ads URLs (catalogs) or ads data (ads).
        Time-outed responses are scraped again. Feed `data_q`."""
        for response in queue_item:
            if not response.ok:
                if response.status_code >= 408:
                    self.target_q.put(response.url)
                    continue

            try:
                if self.scraping == __ads__:
                    data = self.scraper.get_ad_properties(response)
                elif self.scraping == __catalogs__:
                    data = self.scraper.get_catalog_ads(response)

                self.data_q.put(data)

            except Exception:
                msg = 'Can\'t scrape %s: %s' % (self.scraping, response.url)
                logging.exception(msg)
                continue

    def store_data(self, queue_item, databaser):
        """Store adds URLs and add data"""
        # saving URLs
        if isinstance(queue_item, list):
            databaser.insert_multiple(queue_item, databaser.urls)

            self.commit_checker(databaser, queue_item, 5000)

        # saving adds
        else:
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
                    self.old_ads_count += 1

                    if self.old_ads_count > old_items_threshold:
                        logging.warning('Old adds threshold exceeded')
                        self.stop_requesting_e.set()

            # remove add URL from urls table
            databaser.delete(queue_item['ad_id'], databaser.urls)

            self.commit_checker(databaser, queue_item, 2000)

    def get_ads_urls(self):
        """Generate catalogs URLs, store collected ads URLs in the database"""
        self.scraping = __catalogs__

        ads_urls_processor = multiprocessing.Process(target=self.process_data)
        ads_urls_processor.daemon = True

        ads_urls_consumer = multiprocessing.Process(target=self.consume_data)
        ads_urls_consumer.daemon = True

        # TODO: start and end should be taken from the parent script
        catalogs = self.scraper.generate_catalog_urls(start=10, end=0)
        for catalog in catalogs:
            self.target_q.put(catalog)

        ads_urls_processor.start()
        ads_urls_consumer.start()
        self.produce_data()

        self.responses_q.put(__exit__)
        ads_urls_processor.join()

        self.data_q.put(__exit__)
        ads_urls_consumer.join()

        self.empty_queues()

    def get_ads_data(self):
        """Parse ads HTML, store collected data in the database"""
        self.scraping = __ads__

        ads_data_processor = multiprocessing.Process(target=self.process_data)
        ads_data_processor.daemon = True

        ads_data_consumer = multiprocessing.Process(target=self.consume_data)
        ads_data_consumer.daemon = True

        databaser = self.create_databaser()
        for add_url in databaser.urls_get_all():
            self.target_q.put(add_url[0])

        ads_data_processor.start()
        ads_data_consumer.start()
        self.produce_data()

        self.responses_q.put(__exit__)
        ads_data_processor.join()

        self.data_q.put(__exit__)
        ads_data_consumer.join()

        self.empty_queues()


class GeocodingFactory(ProducerConsumer):
    def __init__(self, scraper):
        """
        This class is responsible for geocoding location data which can be
        scraped alongside target data by scrapers.
        Google Geocoding API is used to transform locations to coordinates and
        vice versa. This API has a limit of 5 request per second, so only 5
        addresses are geocoded at once. Currently used IP is switched if its'
        geocoding requests limit is depleted. This IP is also remembered, so it
        can't be used again as it would be worthless.

        So locations to geocode are taken from a given scraper database and
        then loaded to the `target_q`. Location can be a tuple of either a
        `district`, `city` and `locality` for traditional geocoding or
        `latitude` and `longitude` for reverse geocoding.
        These locations are then requested for geocoding using special
        requesting methods which constructs the URL and issue the actual GET
        request. Results are then passed to the `responses_q`. Time-outed
        requests (location related to the request) are put back to the
        `target_q`.
        `responses_q` items are processed accordingly based on what kind of
        location is being geocoded.
        Crunched data are then passed to the `data_q` and stored in a separate
        geocoding (cache-like) database which is shared by all scrapers.

        Incomplete records (i.e. `country` or `region` or `district` is
        missing) are then reverse geocoded by their coordinates to get these
        missing data.

        Finally, if some information are still missing, these kind of records
        are updated based on similar records from the geocoding cache database
        itself.

        1. geocode locations
        scraper database -> target_q -> produce_data() using get_geo() ->
        responses_q -> process_data() using get_coordinates() -> data_q ->
        store_data() -> geocoding database

        2. reverse geocode for missing data
        geocoding database -> target_q -> produce_data() using get_rgeo() ->
        responses_q -> process_data() using get_missing_components() ->
        data_q -> store_data() -> geocoding database

        3. add missing based on self
        geocoding database -> geocoding database

        IP changing and stop requesting are event based.

        :argument scraper: scraper instance
        :type scraper: `:class:Scraper`

        """
        super(GeocodingFactory, self).__init__(scraper=scraper,
                                               processes=geocoding_processes)

        self.scraper = scraper
        self.geocoder = Geocoder()

        self.used_ips = []
        self.databaser_type = __geo__
        self.change_ip_e = multiprocessing.Event()

    def manage_ip(self):
        """Set new IP address if current limit is depleted"""
        if self.change_ip_e.is_set():
            ensure_new_ip(used_ips=self.used_ips, store_all=True)
            self.change_ip_e.clear()

    def collect_data(self, queue_item):
        """Collect and parse geocoding results from `results_q` and put
        collected data to the `data_q`. Set event if IP needs to be changed,
        i.e. geocoding result is None, and put ungeocoded addresses back to
        the `target_q`."""
        for geocoding_response, addr_cmps in queue_item:
            # TODO: investigate 403 occurrences
            if not geocoding_response.ok:
                if geocoding_response.status_code >= 408:
                    self.target_q.put(addr_cmps)

                continue

            self.geocoder.geocoding_result = geocoding_response
            if self.geocoder.geocoding_result is None:
                if not self.change_ip_e.is_set():
                    self.change_ip_e.set()

                self.target_q.put(addr_cmps)
                continue

            try:
                self.geocoder.url = geocoding_response.url

                if len(addr_cmps) == 3:
                    self.geocoder.address_components = addr_cmps
                    location = self.geocoder.get_coordinates()

                elif len(addr_cmps) == 2:
                    self.geocoder.address_coordinates = addr_cmps
                    location = self.geocoder.get_missing_components()

            except Exception:
                msg = ('Can\'t geocode location: %s' % geocoding_response.url)
                logging.exception(msg)
                continue

            else:
                if isinstance(location, tuple):
                    self.target_q.put(location)
                    continue
                elif location is None:
                    continue

                self.data_q.put(location)

    def store_data(self, queue_item, databaser):
        """Store geocoded locations and reverse geocoded completion data"""
        if 'completion' in queue_item:
            del queue_item['completion']
            databaser.complete_record(queue_item)
        else:
            if not databaser.is_stored(queue_item):
                databaser.insert(queue_item)

        self.commit_checker(databaser, queue_item, 100)

    def geocode(self):
        """Put addresses from to_geocode list to the `target_q`. Manage IPs -
        store all used IPs as these can not be re-used, get a new one when
        change_ip_e event is set."""
        ads_databaser = self.create_databaser(__ads__)
        to_geocode = ads_databaser.to_geocode()
        databaser = self.create_databaser(__geo__)

        # TODO: this is just way too slow ...
        for addr_cmps in to_geocode:
            if databaser.is_stored(addr_cmps):
                continue

            self.target_q.put(addr_cmps)

        ensure_new_ip(used_ips=self.used_ips)

        geocoding_processor = multiprocessing.Process(target=self.process_data)
        geocoding_processor.daemon = True
        geocoding_processor.start()

        geocoding_consumer = multiprocessing.Process(target=self.consume_data)
        geocoding_consumer.daemon = True
        geocoding_consumer.start()

        # get coordinates for new addresses
        self.produce_data(requester=get_geo, wait=True)

        incomplete_records = databaser.get_incomplete_records()
        for incomplete_record in incomplete_records:
            self.target_q.put(incomplete_record)

        # add missing localization attributes for cached addresses
        self.produce_data(requester=get_rgeo, wait=True)

        self.responses_q.put(__exit__)
        geocoding_processor.join()

        self.data_q.put(__exit__)
        geocoding_consumer.join()

        self.empty_queues()

        # TODO: successful only on second run - debug why
        databaser.update_record_from_self()

        # TODO: this maybe should not be here (add to docstring if it should)
        ads_databaser.update_location_data()