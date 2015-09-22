#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Shared networking functions"""


import logging
import requests

from stem import Signal
from stem.control import Controller
from time import sleep
from random import randint

from util.alphanumericker import string_to_ascii, comparable_string
from util.configparser import (get_tor_port, get_tor_password,
                               get_geocoding_language)


#:
tor_port = get_tor_port()
tor_password = get_tor_password()
geocoding_language = get_geocoding_language()

geocoding_url = 'http://maps.googleapis.com/maps/api/geocode/json'


def get(url, timeout=15, params=None):
    """GET data from specified URL

    :argument url: web site address
    :type url: str
    :argument timeout: request timeout
    :type timeout: int
    :argument params: URL parameters
    :type params: dict

    :returns `requests.Response` instance

    """
    url = url.strip()
    http_proxy = {'http': '127.0.0.1:8118'}
    user_agent = 'scrape-me-again'

    try:
        response = requests.get(url=url,
                                params=params,
                                timeout=timeout,
                                proxies=http_proxy,
                                headers={'User-Agent': user_agent})
    except requests.exceptions.Timeout:
        response = requests.Response()
        response.url = url
        response.status_code = 408

    log_level = logging.debug
    if not response.ok:
        log_level = logging.error

    log_level('%s - %s' % (response.status_code, response.url))

    return response


def get_geo(address):
    """Geocode specified address

    :argument address: address components
    :type address: tuple

    :returns tuple

    """
    params = {'language': geocoding_language}

    district, city, locality = address
    if locality is None:
        params['address'] = city
    else:
        ccity = comparable_string(city)
        clocl = comparable_string(locality)

        if ccity in clocl:
            params['address'] = locality
        else:
            params['address'] = city + ',' + locality

    if (locality is None) and (district is not None):
        params['components'] = 'administrative_area:%s' % district

    for param in ('address', 'components'):
        if param not in params:
            continue

        params[param] = params[param].replace(' ', '+')
        params[param] = string_to_ascii(params[param])

    result = get(url=geocoding_url, params=params)
    return result, address


def get_rgeo(coordinates):
    """Geocode specified coordinates

    :argument coordinates: address coordinates
    :type coordinates: tuple

    :returns tuple

    """
    params = {'language': geocoding_language,
              'latlng': ','.join([str(crdnt) for crdnt in coordinates])}

    result = get(url=geocoding_url, params=params)
    return result, coordinates


def get_current_ip():
    """GET current IP address

    :returns str or None

    """
    url = 'http://icanhazip.com/'
    current_ip = get(url=url, timeout=5)

    if current_ip.ok:
        return current_ip.text.strip()
    else:
        return None


def set_new_ip():
    """Change IP using TOR"""
    with Controller.from_port(port=tor_port) as controller:
        controller.authenticate(password=tor_password)
        controller.signal(Signal.NEWNYM)
    sleep(1)


def ip_is_usable(used_ips, current_ip, store_all=False):
    """Manage a list of already used IPs

    :argument used_ips: dynamically changing list of IPs
    :type used_ips: list
    :argument current_ip: current IP address
    :type current_ip: str
    :argument store_all: flag to store all used IPs, not just 10
    :type store_all: bool

    :returns bool

    """
    usable = False
    if current_ip not in used_ips:
        if store_all:
            used_ips.append(current_ip)
        elif len(used_ips) == 10:
            used_ips.append(current_ip)
            del used_ips[0]
        else:
            used_ips.append(current_ip)

        usable = True

    return usable


def ensure_new_ip(used_ips, store_all=False):
    """Ensure the newly set IP is usable

    :argument used_ips: dynamically changing list of IPs
    :type used_ips: list

    """
    ok_ip = False

    while not ok_ip:
        current_ip = get_current_ip()
        if current_ip is None:
            set_new_ip()
            continue

        ip_usable = ip_is_usable(used_ips, current_ip, store_all)
        if not ip_usable:
            set_new_ip()
            continue

        ok_ip = True
