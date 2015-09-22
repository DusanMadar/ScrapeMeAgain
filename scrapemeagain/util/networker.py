# -*- coding: utf-8 -*-


"""Shared networking functions"""


import logging
import requests

from stem import Signal
from stem.control import Controller
from time import sleep

from alphanumericker import string_to_ascii, comparable_string
from configparser import (get_tor_port, get_tor_password,
                          get_geocoding_language)


IP_GETTER_URL = 'http://icanhazip.com/'
GEOCODING_URL = 'http://maps.googleapis.com/maps/api/geocode/json'


#:
tor_port = get_tor_port()
tor_password = get_tor_password()
geocoding_language = get_geocoding_language()
REAL_IP = requests.get(IP_GETTER_URL).content


def get(url, timeout=15, params=None, log=True):
    """GET data from specified URL

    :argument url: web site address
    :type url: str
    :argument timeout: request timeout
    :type timeout: int
    :argument params: URL parameters
    :type params: dict
    :argument log: flag to log activity
    :type log: bool

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
    except (requests.exceptions.Timeout,
            # TODO: why the heck is this happening?
            requests.exceptions.ConnectionError) as exc:
        response = requests.Response()
        response.url = url

        if isinstance(exc, requests.exceptions.Timeout):
            response.status_code = 408
        else:
            # the status code is misleading - it is used for ConnectionError
            response.status_code = 409

    if log:
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

    result = get(url=GEOCODING_URL, params=params)
    return result, address


def get_rgeo(coordinates):
    """Geocode specified coordinates

    :argument coordinates: address coordinates
    :type coordinates: tuple

    :returns tuple

    """
    params = {'language': geocoding_language,
              'latlng': ','.join([str(crdnt) for crdnt in coordinates])}

    result = get(url=GEOCODING_URL, params=params)
    return result, coordinates


def get_current_ip():
    """GET current IP address

    :returns str or None

    """
    current_ip = get(url=IP_GETTER_URL, timeout=5, log=False)

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
    :argument store_all: flag to store all used IPs
    :type store_all: bool

    :returns bool

    """
    # never use real IP
    if current_ip == REAL_IP:
        return False

    # do dot allow IP reuse
    if current_ip in used_ips:
        return False

    # register IP
    used_ips.append(current_ip)

    if not store_all:
        # TODO: used IP number should be taken from configuration file
        if len(used_ips) == 10:
            del used_ips[0]

    logging.info('New IP: {ip}'.format(ip=current_ip))

    return True


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
