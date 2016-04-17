# ScrapeMeAgain
ScrapeMeAgain is a Python 2.7 powered web scraper. It uses multiprocessing to get the work done quicker and stores collected data in a [SQLite](http://www.sqlite.org/) database.

## Geocoding
There is a **geocoding** module for transforming location data to coordinates.
Also, a helper script for **spatially enabling a SQLite database** is present. This script actually converts the SQLite database to a Spatialite database by adding a 2D geometry (Point) column in WGS-84 and all other Spatialite required stuff.

## System requirements
ScrapeMeAgain leverages `Tor` and `Privoxy`.

[Tor](https://www.torproject.org/) in combination with [Privoxy](http://www.privoxy.org/) are used for anonymity (i.e. regular IP address changes). Follow this guide for detailed information about installation and configuration: [Crawling anonymously with Tor in Python](http://sacharya.com/crawling-anonymously-with-tor-in-python/).

## Usage
You have to provide your own database table description and an actual scraping script which must follow the `BaseScraper` interface.
