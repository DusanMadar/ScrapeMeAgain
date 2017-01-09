# -*- coding: utf-8 -*-


"""Multiprocess I/O intensive tasks to maximize performance"""


import abc
import time
import logging
import multiprocessing

from geocoder import Geocoder
from databaser import AdsDatabaser, GeoDatabaser
from util.alphanumericker import current_date_time_stamp
from util.networker import ensure_new_ip, get, get_geo, get_rgeo
from util.configparser import (get_scrape_processes, get_geocoding_processes,
                               get_old_items_threshold)


#: constants
GEO = 'geo'
ADS = 'ads'
EXIT = 'exit'
CATALOGS = 'catalogs'
SCRAPE_PROCESSES = get_scrape_processes()
GEOCODING_PROCESSES = get_geocoding_processes()
OLD_ITEMS_THRESHOLD = get_old_items_threshold()


def inform(message):
    """Both log and print an info message

    :argument scraper: scraper instance
    :type scraper: `:class:Scraper`

    """
    logging.info(message)
    print '{0} {1}'.format(current_date_time_stamp(), message)


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

        Stop issuing requests and commit forcing are event based actions.
        Processes share data using queues, where 'exit' is a signal to stop.

        :argument scraper: scraper instance
        :type scraper: `:class:Scraper`
        :argument processes: number of processes to be used
        :type processes: int

        """
        self.scraper = scraper
        self.used_ips = []

        self.databaser_type = None
        self.transaction_items = 0

        self.target_q = multiprocessing.Queue()
        self.responses_q = multiprocessing.Queue()
        self.data_q = multiprocessing.Queue()

        self.queues = [('target_q', self.target_q),
                       ('responses_q', self.responses_q),
                       ('data_q', self.data_q)]

        self.change_ip_e = multiprocessing.Event()
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
        """Store data - what checks should be performed and where to save.
        This method also MUST handle COMMITTING changes."""
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

        elif databaser_type == ADS:
            dtbsr = AdsDatabaser(self.scraper.db_file, self.scraper.db_table)

        elif databaser_type == GEO:
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
                time.sleep(1)

                if self.change_ip_e.is_set():
                    # wait till the new IP is set
                    pass
                elif idle_since is None:
                    idle_since = time.time()
                else:
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

            if queue_item == EXIT:
                break

            self.collect_data(queue_item)

    def consume_data(self):
        """Write processed data from the `data_q` to the database. Given
        implementation of the `store_data` method knows exactly what to do and
        where the data should be stored eventually."""
        databaser = self.create_databaser()
        geo_databaser = self.create_databaser(GEO)

        while True:
            if self.data_q.qsize() == 0:
                time.sleep(1)
                continue

            queue_item = self.data_q.get()
            if queue_item == EXIT:
                break

            try:
                # not all store_data() implementations expect 4 arguments
                try:
                    self.store_data(queue_item, databaser, geo_databaser)
                except TypeError:
                    self.store_data(queue_item, databaser)
            except Exception:
                logging.exception('Failed consuming data')
                continue

        if self.transaction_items > 0:
            databaser.commit()
            self.transaction_items = 0


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
                                         processes=SCRAPE_PROCESSES)

        self.scraping = None
        self.old_ads_count = 0
        self.databaser_type = ADS

    def manage_ip(self):
        """Set new IP address after each bunch of requests.

        Handle the `change_ip_e` event as changing the IP might take quite
        a long time, i.e. longer than are thresholds for stop requesting new
        data.

        The main data processing process will not terminate while the
        `change_ip_e` event is set.

        """
        self.change_ip_e.set()
        ensure_new_ip(used_ips=self.used_ips)
        self.change_ip_e.clear()

    def collect_data(self, queue_item):
        """Collect and process ads URLs (catalogs) or ads data (ads).
        Time-outed responses are scraped again. Feed `data_q`."""
        for response in queue_item:
            if not response.ok:
                if response.status_code >= 408:
                    self.target_q.put(response.url)
                    continue

            try:
                if self.scraping == ADS:
                    data = self.scraper.get_ad_properties(response)
                elif self.scraping == CATALOGS:
                    data = self.scraper.get_catalog_ads(response)

                self.data_q.put(data)

            except Exception:
                msg = 'Can\'t scrape %s: %s' % (self.scraping, response.url)
                logging.exception(msg)
                continue

    def _add_location(self, geo_databaser, queue_item):
        if geo_databaser:
            addr_cmps = (queue_item.get('district', None),
                         queue_item.get('city', None),
                         queue_item.get('locality', None))

            location = geo_databaser.is_stored(addr_cmps, return_location=True)
            if location is not None:
                location_data = {
                    'country': location.country,
                    'region': location.region,
                    'district': location.district,
                    'city': location.city,
                    'locality': location.locality,
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'location_id': location.ID
                }

                queue_item.update(location_data)

    def store_data(self, queue_item, databaser, geo_databaser=None):
        """Store adds URLs and add data"""
        # saving URLs
        if isinstance(queue_item, list):
            databaser.insert_multiple(queue_item, databaser.urls)

            self.commit_checker(databaser, queue_item, 10000)

        # saving adds
        else:
            # ad not found - remove if was stored during previous scrapes
            if len(queue_item) == 1:
                if databaser.is_stored(queue_item['ad_id']):
                    databaser.delete(queue_item['ad_id'])

            # new ad
            elif not databaser.is_stored(queue_item['ad_id']):
                # get the ad location from Geocodingcahe
                self._add_location(geo_databaser, queue_item)

                databaser.insert(queue_item)

            else:
                db_ts = databaser.get_timestamp(queue_item['ad_id'])

                # updated ad
                if queue_item['last_update'] > db_ts:
                    databaser.update(data=queue_item)
                # old ad
                else:
                    self.old_ads_count += 1

                    if self.old_ads_count > OLD_ITEMS_THRESHOLD:
                        logging.warning('Old adds threshold exceeded')
                        self.stop_requesting_e.set()

            # remove add URL from urls table
            databaser.delete(queue_item['ad_id'], databaser.urls)

            self.commit_checker(databaser, queue_item, 2000)

    def get_ads_urls(self):
        """Generate catalogs URLs, store collected ads URLs in the database"""
        self.scraping = CATALOGS

        ads_urls_processor = multiprocessing.Process(target=self.process_data)
        ads_urls_processor.daemon = True

        ads_urls_consumer = multiprocessing.Process(target=self.consume_data)
        ads_urls_consumer.daemon = True

        for catalog in self.scraper.generate_catalog_urls():
            self.target_q.put(catalog)

        #:
        inform('Downloading ads URLs ...')

        ads_urls_processor.start()
        ads_urls_consumer.start()
        self.produce_data()

        self.responses_q.put(EXIT)
        ads_urls_processor.join()

        self.data_q.put(EXIT)
        ads_urls_consumer.join()

        self.empty_queues()

    def get_ads_data(self):
        """Parse ads HTML, store collected data in the database"""
        self.scraping = ADS

        ads_data_processor = multiprocessing.Process(target=self.process_data)
        ads_data_processor.daemon = True

        ads_data_consumer = multiprocessing.Process(target=self.consume_data)
        ads_data_consumer.daemon = True

        databaser = self.create_databaser()
        for add_url in databaser.urls_get_all():
            self.target_q.put(add_url[0])

        #:
        inform('Downloading ads data ...')

        ads_data_processor.start()
        ads_data_consumer.start()
        self.produce_data()

        self.responses_q.put(EXIT)
        ads_data_processor.join()

        self.data_q.put(EXIT)
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
                                               processes=GEOCODING_PROCESSES)

        self.geocoder = Geocoder()

        self.used_ips = []
        self.databaser_type = GEO

    def manage_ip(self):
        """Set new IP address if geocoding requests limit for the current one
        is depleted"""
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
        ensure_new_ip(used_ips=self.used_ips)

        ads_databaser = self.create_databaser(ADS)
        geo_databaser = self.create_databaser(GEO)

        #:
        inform('Loading locations ...')

        # index on 'valid_for' will (maybe) sped-up the .is_stored() check
        geo_databaser.create_index('valid_for')
        # TODO: this is just way too slow ... but multiprocessing isn't an
        # option with sqlite
        for addr_cmp in ads_databaser.to_geocode():
            if geo_databaser.is_stored(addr_cmp):
                continue

            self.target_q.put(addr_cmp)

        geocoding_processor = multiprocessing.Process(target=self.process_data)
        geocoding_processor.daemon = True
        geocoding_processor.start()

        geocoding_consumer = multiprocessing.Process(target=self.consume_data)
        geocoding_consumer.daemon = True
        geocoding_consumer.start()

        #:
        inform('Geocoding locations ...')

        # get coordinates for new addresses, make sure everything is committed
        self.produce_data(requester=get_geo, wait=True)
        geo_databaser.commit()

        for incomplete_record in geo_databaser.get_incomplete_records():
            self.target_q.put(incomplete_record)

        #:
        inform('Reverse geocoding incomplete locations ...')

        # add missing localization attributes for cached addresses
        self.produce_data(requester=get_rgeo, wait=True)

        self.responses_q.put(EXIT)
        geocoding_processor.join()

        self.data_q.put(EXIT)
        geocoding_consumer.join()

        self.empty_queues()

        geo_databaser.update_record_from_self()

        #:
        inform('Merging locations to ads data ...')
        # TODO: this maybe should not be here (add to docstring if it should)
        ads_databaser.update_location_data()
        #:
        inform('Done')
