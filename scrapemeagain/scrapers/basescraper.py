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
    @abc.abstractproperty
    def list_urls_range(self):
        """Upper and lower range/interval bounds for list URLs, e.g. [10, 0)

        :returns tuple
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

    @property
    def list_urls_count(self):
        return abs(self.list_urls_range[0] - self.list_urls_range[1])
