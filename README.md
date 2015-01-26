# scrape-me-again
> WORK STILL IN PROGRESS - some files are still missing ...

*scrape-me-again is yeat another web scraping application written in Python.*

It uses **multiprocessing** heavily to get the work done quicker. [TOR](https://www.torproject.org/) in combination with [privoxy](http://www.privoxy.org/) is used for anonymity. Collected data are stored in a [SQLite](http://www.sqlite.org/) database, which structure is defined using [SQLAlchemy](http://www.sqlalchemy.org/).

There is a **geocoding** module if you would like to get coordinates for your collected data.

## Requirements
* SQLAlchemy==0.9.7
* argparse==1.2.1
* beautifulsoup4==4.3.2
* lxml==3.3.5
* requests==2.3.0
* stem==1.2.2
* wsgiref==0.1.2

## Guide for TOR and privoxy setup
[Crawling anonymously with Tor in Python](http://sacharya.com/crawling-anonymously-with-tor-in-python/)
