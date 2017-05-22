"""Common API definition for all scraper classes."""


import abc


class BaseScraper(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def base_url(self):
        """Target web site base address."""
        raise NotImplementedError()

    @abc.abstractproperty
    def list_url_template(self):
        """Target web site list page URL template."""
        raise NotImplementedError()

    @abc.abstractproperty
    def db_file(self):
        """SQLite file name."""
        raise NotImplementedError()

    @abc.abstractproperty
    def db_table(self):
        """SQLAlchemy table reference."""
        raise NotImplementedError()

    @abc.abstractmethod
    def generate_list_urls(self):
        """Generate list pages URLs.

        :returns iterator
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_lists_count(self):
        """Get lists count from the first list page pagination.

        :returns int
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_item_urls(self, response):
        """Get item URLs from a given list page.

        :argument response: list page
        :type response: `requests.Response`

        :returns
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_item_properties(self, response):
        """Get item properties.

        :argument response:
        :type response: `requests.Response`

        :returns dict
        """
        raise NotImplementedError()
