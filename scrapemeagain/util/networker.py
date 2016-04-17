# -*- coding: utf-8 -*-


"""Shared networking functions"""


import os
import json
import ipaddr
import logging
import requests

from stem import Signal
from stem.control import Controller
from time import sleep
from random import choice

from alphanumericker import string_to_ascii, comparable_string
from configparser import (get_tor_port, get_tor_password,
                          get_geocoding_language, get_used_ips)


# Useful URLs
IP_GETTER_URL = 'http://icanhazip.com/'
GEOCODING_URL = 'http://maps.googleapis.com/maps/api/geocode/json'


# Configuration
TOR_PORT = get_tor_port()
TOR_PASSWORD = get_tor_password()
USED_IPS_BUFFER_SIZE = get_used_ips()
GEOCODING_LANGUAGE = get_geocoding_language()
REAL_IP = requests.get(IP_GETTER_URL).content

# User agents
try:
    USER_AGENTS = []

    # NOTE: `user_agents.json` must be colocated with this file
    user_agents_json = os.path.join(os.path.dirname(__file__),
                                    'user_agents.json')

    with open(user_agents_json) as file_object:
        user_agents_data = json.load(file_object)

    for operating_system in user_agents_data.values():
        for user_agent in operating_system.values():
            USER_AGENTS.append(user_agent)

    if not USER_AGENTS:
        raise ValueError('No user agents')

except Exception as exc:
    USER_AGENTS = 'ScrapeMeAgain'
    logging.warning('Loading/reading user agents from JSON failed.\n'
                    'Details: {details}\n'
                    'Using default user agent: "{user_agents}"'
                    .format(user_agents=USER_AGENTS, details=exc.message))


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

    local_proxy = '127.0.0.1:8118'
    http_proxy = {'http': local_proxy,
                  'https': local_proxy}

    if isinstance(USER_AGENTS, list):
        user_agent = choice(USER_AGENTS)
    else:
        user_agent = USER_AGENTS

    try:
        response = requests.get(url=url,
                                params=params,
                                timeout=timeout,
                                proxies=http_proxy,
                                headers={'User-Agent': user_agent},
                                verify=False)
    except Exception as exc:
        # don't fail on any exception, setup a fake response instead
        response = requests.Response()
        response.url = url

        if isinstance(exc, requests.exceptions.Timeout):
            response.status_code = 408
        else:
            response.status_code = 503

    if log:
        log_level = logging.debug
        if not response.ok:
            log_level = logging.error

        log_level('{status} - {url}'.format(status=response.status_code,
                                            url=response.url))

    return response


def get_geo(address):
    """Geocode specified address

    :argument address: address components
    :type address: tuple

    :returns tuple

    """
    params = {'language': GEOCODING_LANGUAGE}

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
    params = {'language': GEOCODING_LANGUAGE,
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
    with Controller.from_port(port=TOR_PORT) as controller:
        controller.authenticate(password=TOR_PASSWORD)
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
    # consider only IP addresses
    try:
        ipaddr.IPAddress(current_ip)
    except ValueError:
        return False

    # never use real IP
    if current_ip == REAL_IP:
        return False

    # do dot allow IP reuse
    if current_ip in used_ips:
        return False

    # register IP
    used_ips.append(current_ip)

    if not store_all:
        if len(used_ips) == USED_IPS_BUFFER_SIZE:
            del used_ips[0]

    logging.info('New IP: {ip}'.format(ip=current_ip))

    return True


def ensure_new_ip(used_ips, store_all=False):
    """Ensure the newly set IP is usable

    :argument used_ips: dynamically changing list of IPs
    :type used_ips: list

    """
    while True:
        current_ip = get_current_ip()
        if current_ip is None:
            set_new_ip()
            continue

        ip_usable = ip_is_usable(used_ips, current_ip, store_all)
        if not ip_usable:
            set_new_ip()
            continue

        break
