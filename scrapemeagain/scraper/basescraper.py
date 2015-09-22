# -*- coding: utf-8 -*-


"""Common API definition for all scraper classes"""


import abc


class BaseScraper(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def base_url(self):
        """Target web site base address"""
        raise NotImplementedError()

    @abc.abstractproperty
    def catalog_url(self):
        """Target web site catalog pattern"""
        raise NotImplementedError()

    @abc.abstractproperty
    def db_file(self):
        """SQLite file name"""
        raise NotImplementedError()

    @abc.abstractproperty
    def db_table(self):
        """SQLAlchemy table reference"""
        raise NotImplementedError()

    @abc.abstractmethod
    def generate_catalog_urls(self):
        """Generate catalog URLs

        :returns generator

        """
        raise NotImplementedError()

    @abc.abstractmethod
    def ad_id(self, url):
        """Get an ad ID from its URL

        :argument url: page address
        :type url: str

        :returns int

        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_catalogs_count(self):
        """Get all catalogs count from first catalog URL

        :returns int

        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_catalog_ads(self, response):
        """Get list of ads URLs from the catalog

        :argument response:
        :type response: `requests.Response`

        :returns dict

        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_ad_properties(self, response):
        """Get ad properties

        :argument response:
        :type response: `requests.Response`

        :returns dict

        """
        raise NotImplementedError()
