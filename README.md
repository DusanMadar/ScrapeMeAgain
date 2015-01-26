# scrape-me-again
> WORK IN PROGRESS - some files are still missing ...

*scrape-me-again is yet another web scraping application written in Python.*

It uses **multiprocessing** heavily to get the work done quicker. [TOR](https://www.torproject.org/) in combination with [privoxy](http://www.privoxy.org/) is used for anonymity. Follow this guide for more information: [Crawling anonymously with Tor in Python](http://sacharya.com/crawling-anonymously-with-tor-in-python/).

Collected data are stored in a [SQLite](http://www.sqlite.org/) database, which structure is defined using [SQLAlchemy](http://www.sqlalchemy.org/).

There is a **geocoding** module if you would like to get coordinates for your collected data.

## Requirements
* Python 2.7.6
* SQLAlch.emy==0.9.7
* argparse==1.2.1
* beautifulsoup4==4.3.2
* lxml==3.3.5
* requests==2.3.0
* stem==1.2.2
* wsgiref==0.1.2

