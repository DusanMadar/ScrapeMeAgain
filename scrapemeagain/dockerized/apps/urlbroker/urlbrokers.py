from scrapemeagain.config import Config


class UrlsRangeManager:
    def __init__(self, descending=True):
        self._urls_range = None
        self.descending = descending

    def get_urls_count(self):
        return 0

    def generate_urls_range(self):
        urls_count = self.get_urls_count()
        step = urls_count // Config.SCRAPERS_COUNT

        for i in range(urls_count, 0, -step):
            start = i
            end = i - step
            if end < step:
                end = 0

            # The returned range is expected to be processed in descending
            # order: start > end, e.g. (100, 0); unless the `descending`
            # flag is unset: start < end, e.g. (0, 100).
            yield (start, end) if self.descending else (end, start)

            if end == 0:
                break

    def get_urls_range(self):
        if self._urls_range is None:
            self._urls_range = self.generate_urls_range()

        try:
            return next(self._urls_range)
        except StopIteration:
            return (0, 0)


class ListUrlsBroker(UrlsRangeManager):
    def __init__(self, scraper):
        super().__init__()

        self.scraper = scraper

    def get_urls_count(self):
        return self.scraper.get_lists_count()
