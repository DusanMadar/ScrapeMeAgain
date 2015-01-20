#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Common API definition for all scraper classes"""


import abc

NOT_IMPLEMETED = 'Method not implemented'


class BaseScraper(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def base_url(self):
        """Target web site base address"""
        raise NotImplementedError(NOT_IMPLEMETED)

    @abc.abstractproperty
    def catalog_url(self):
        """Target web site catalog pattern"""
        raise NotImplementedError(NOT_IMPLEMETED)

    @abc.abstractproperty
    def db_file(self):
        """SQLite file name with extension"""
        raise NotImplementedError(NOT_IMPLEMETED)

    @abc.abstractproperty
    def db_table(self):
        """SQLAlchemy table reference"""
        raise NotImplementedError(NOT_IMPLEMETED)

    @abc.abstractmethod
    def generate_catalog_urls(self, start, end, step=-1):
        """Generate a list of catalog URLs

        :argument start: first catalog number
        :type start: int
        :argument end: last catalog number
        :type end: int
        :argument step: indicates if scrape from the first or last catalog
        :type step: int

        :returns list

        """
        raise NotImplementedError(NOT_IMPLEMETED)

    @abc.abstractmethod
    def ad_id(self, url):
        """Get an ad ID from its URL

        :argument url: page address
        :type url: str

        :returns int

        """
        raise NotImplementedError(NOT_IMPLEMETED)

    @abc.abstractmethod
    def get_catalog_ads(self, response):
        """Get list of ads URLs from the catalog

        :argument response:
        :type response: `requests.Response`

        :returns dict

        """
        raise NotImplementedError(NOT_IMPLEMETED)

    @abc.abstractmethod
    def get_ad_properties(self, response):
        """Get ad properties

        :argument response:
        :type response: `requests.Response`

        :returns dict

        """
        raise NotImplementedError(NOT_IMPLEMETED)
