# ScrapeMeAgain

ScrapeMeAgain is a Python 3 powered web scraper. It uses multiprocessing to get the work done quicker and stores collected data in an [SQLite](http://www.sqlite.org/) database.

## Docker support

I have started to 'dockerize' the scraper. Work still in progress - checkout branch [dockerized](https://github.com/DusanMadar/ScrapeMeAgain/tree/dockerized) for more (interin - things may change!) details.

The idea is to run one scrapere instance per container (with a single master scraper). This way it will be possible to use multiple Tor IPs at the same time and, unless you abuse it, scrape data faster.

## System requirements
ScrapeMeAgain leverages `Tor` and `Privoxy`.

[Tor](https://www.torproject.org/) in combination with [Privoxy](http://www.privoxy.org/) are used for anonymity (i.e. regular IP address changes). For more details about installation and configuration refer to:
 * [A step-by-step guide how to use Python with Tor and Privoxy](https://gist.github.com/DusanMadar/8d11026b7ce0bce6a67f7dd87b999f6b)
 * [Crawling anonymously with Tor in Python](http://sacharya.com/crawling-anonymously-with-tor-in-python/) ([alternative link (Gist)](https://gist.github.com/KhepryQuixote/46cf4f3b999d7f658853))

## Usage
You have to provide your own database table description and an actual scraper class which must follow the `BaseScraper` interface. See `scrapemeagain/scrapers/examplescraper` for more details.

Use `python scrapemeagain/scrapers/examplescraper/main.py` to run the `examplescraper` from command line.

## Legacy
The Python 2.7 version of ScrapeMeAgain, which also provides geocoding capabilities, is available under the `legacy` branch and is no longer maintained.
