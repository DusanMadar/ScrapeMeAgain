# ScrapeMeAgain
**work in progress**

ScrapeMeAgain is a Python 3 powered web scraper. It uses multiprocessing to get the work done quicker and stores collected data in a [SQLite](http://www.sqlite.org/) database.

## System requirements
ScrapeMeAgain leverages `Tor` and `Privoxy`.

[Tor](https://www.torproject.org/) in combination with [Privoxy](http://www.privoxy.org/) are used for anonymity (i.e. regular IP address changes). Follow this guide for detailed information about installation and configuration: [Crawling anonymously with Tor in Python](http://sacharya.com/crawling-anonymously-with-tor-in-python/).

## Usage
You have to provide your own database table description and an actual scraping script which must follow the `BaseScraper` interface. See `scrapemeagain/scrapers/examplescraper` for more details.
