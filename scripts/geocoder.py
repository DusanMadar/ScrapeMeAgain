#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Change addresses to coordinates and vice versa"""


import difflib
import logging
from collections import OrderedDict

from util.configparser import (get_ungeocoded_coordinate,
                               get_ungeocoded_component)
from util.addresser import normalize_address, comparable_address
from util.alphanumericker import (comparable_string, iterable_to_string,
                                  float_precision)


#:
ungeocoded_coordinate = get_ungeocoded_coordinate()
ungeocoded_component = get_ungeocoded_component()


class Geocoder(object):
    #: Note on the terminology:
    #: prefix 'r_' -> requested data
    #: prefix 'g_' -> geocoded data
    #: abbreviation 'cmp' -> component

    missing_cmps_types = [('administrative_area_level_1', 'region'),
                          ('administrative_area_level_2', 'district')]

    def __init__(self):
        self.url = None
        self._result = None
        self._addr_cmps = None
        self._addr_crdnts = None

        self.partial_cache = {}

    def _set_ungeocoded(self):
        """Use specific coordinates for addresses that can't be geocoded"""
        self.address_components['latitude'] = ungeocoded_coordinate
        self.address_components['longitude'] = ungeocoded_coordinate

        valid_for = comparable_address(self.address_components)
        self.address_components['valid_for'] = valid_for

    def _precision(self, coordinates):
        """Get coordinates floating precision

        :argument coordinates: latitude and longitude
        :type coordinates: tuple

        :return int

        """
        precisions = [float_precision(crdnt) for crdnt in coordinates]

        return max(precisions)

    def _clear_from_cache(self, coordinates, result):
        """Clear coordinates from partial cache and reset original coordinates

        :argument coordinates: latitude and longitude
        :type coordinates: tuple
        :argument result: collected data
        :type result: dict

        """
        remove_item = None
        for key, values in self.partial_cache.items():
            if coordinates in values:
                result['latitude'] = key[0]
                result['longitude'] = key[1]

                remove_item = key
                break

        if remove_item is not None:
            del self.partial_cache[remove_item]

    def locality_is_valid(self, r_locl, g_locl):
        """Test if requested locality and locality returned by geocoding can be
        considered equal. Test diff percetage first, then abbreviations.

        :argument r_locl: requested locality
        :type r_locl: str
        :argument g_locl: geocoded locality
        :type g_locl: str

        :returns bool

        """
        cr_locl = comparable_string(r_locl)
        cg_locl = comparable_string(g_locl)

        comparison = difflib.SequenceMatcher(None, cr_locl, cg_locl)
        comparison_ratio = comparison.ratio()

        equal = False
        comparision_treshold = 0.65

        if comparison_ratio > comparision_treshold:
            equal = True
        elif comparison_ratio > comparision_treshold - 0.1:
            r_locl_parts = r_locl.split()

            score = 0
            for part in r_locl_parts:
                part = comparable_string(part)

                if part in cg_locl:
                    score += 1

            if score == len(r_locl_parts):
                equal = True

        if not equal:
            # manage abbreviations, like L. Strura, Gen. M. R. Stefanika, ...
            if '.' in cr_locl:
                r_locl_parts = r_locl.split('.')

                main_part = r_locl_parts[-1]
                main_part = comparable_string(main_part)

                if main_part in cg_locl:
                    score = 0
                    for part in r_locl_parts[:-1]:
                        part = comparable_string(part)

                        if part in cg_locl:
                            score += 1

                    if score == len(r_locl_parts[:-1]):
                        equal = True

            # e.g. Trieda Snp -> Trieda Slovenského národného povstania
            else:
                r_locl_parts = r_locl.split()
                r_locl_parts_len = [len(p) for p in r_locl_parts]

                max_part_len = 0
                main_part_index = 0
                for index, part_len in enumerate(r_locl_parts_len):
                    if part_len > max_part_len:
                        max_part_len = part_len
                        main_part_index = index

                main_part = comparable_string(r_locl_parts[main_part_index])
                if main_part in cg_locl:
                    for part in r_locl_parts:
                        part = comparable_string(part)
                        len_part = len(part)

                        if len_part <= 5:
                            score = 0
                            for char in part:
                                if char in cg_locl:
                                    score += 1

                            if score == len_part:
                                equal = True

        return equal

    def _collect_location_data(self, result):
        """Collect desired location data

        :argument result: geocoding result
        :type result: dict

        :return dict

        """
        g_addr_num = []
        location_data = {'latitude': result['geometry']['location']['lat'],
                         'longitude': result['geometry']['location']['lng']}

        for addr_cmp in reversed(result['address_components']):
            cmp_types = addr_cmp['types']
            cmp_name = addr_cmp['long_name']

            if 'postal_code' in cmp_types:
                location_data['postcode'] = cmp_name

            elif 'country' in cmp_types:
                location_data['country'] = cmp_name

            elif 'administrative_area_level_1' in cmp_types:
                location_data['region'] = cmp_name

            elif 'administrative_area_level_2' in cmp_types:
                location_data['district'] = cmp_name

            elif 'locality' in cmp_types:
                location_data['city'] = cmp_name

            elif ('route' in cmp_types or
                  'sublocality' in cmp_types or
                  'neighborhood' in cmp_types):
                location_data['locality'] = cmp_name

                short = addr_cmp['short_name']
                if short != cmp_name:
                    location_data['locality_short'] = short

            elif 'establishment' in cmp_types:
                location_data['establishment'] = cmp_name

            elif 'premise' in cmp_types:
                r_locality = self.address_components['locality']

                if r_locality is None:
                    continue

                if cmp_name not in r_locality:
                    continue

                g_addr_num.append(cmp_name)

            elif 'street_number' in cmp_types:
                g_addr_num.append(cmp_name)

        # update address number
        if g_addr_num:
            if len(g_addr_num) == 2:
                g_addr_num = '/'.join(g_addr_num)
            else:
                g_addr_num = g_addr_num[0]

            if 'locality' in location_data:
                location_data['locality'] += ' ' + g_addr_num
            else:
                location_data['locality'] = g_addr_num

        # remove duplicates
        try:
            g_locl = comparable_string(location_data['locality'])
            g_city = comparable_string(location_data['city'])

            if g_city == g_locl:
                del location_data['locality']
        except KeyError:
            pass

        return location_data

    def _verify_location_data(self, location_data):
        """Verify collected location data

        :argument location_data: collected location data
        :type location_data: dict

        :return dict or None

        """
        try:
            g_city = comparable_string(location_data['city'])
            r_city = comparable_string(self.address_components['city'])

            # city must be always correct
            if g_city != r_city:
                return
        except KeyError:
            return

        if self.address_components['locality'] is not None:
            if 'locality' not in location_data:
                # locality was requested, but was not geocoded
                return

            g_locl = location_data['locality']
            r_locl = self.address_components['locality']

            if not self.locality_is_valid(r_locl, g_locl):
                locality_not_valid = True

                if 'locality_short' in location_data:
                    short = location_data['locality_short']

                    if self.locality_is_valid(r_locl, short):
                        locality_not_valid = False

                if 'establishment' in location_data:
                    estab = location_data['establishment']

                    if self.locality_is_valid(r_locl, estab):
                        location_data['locality'] = estab
                        locality_not_valid = False

                if locality_not_valid:
                    cr_city = comparable_string(r_city)
                    cr_locl = comparable_string(r_locl)

                    if cr_city in cr_locl:
                        r_locl = cr_locl.replace(cr_city, '')

                        if self.locality_is_valid(r_locl, g_locl):
                            locality_not_valid = False

                if locality_not_valid:
                    address = iterable_to_string(self.address_components, True)
                    logging.warning('Locality not valid for: %s\n%s' %
                                    (address, self.url))
                    return

        try:
            for key in ('establishment', 'locality_short'):
                del location_data[key]
        except KeyError:
            pass

        return location_data

    def get_coordinates(self):
        """Collect and verify location data

        :return dict or None

        """
        if self.geocoding_result is None:
            return

        elif self.geocoding_result == 0:
            self._set_ungeocoded()
            return self.address_components

        else:
            for result in self.geocoding_result['results']:
                location_data = self._collect_location_data(result)
                location_data = self._verify_location_data(location_data)

                if location_data is not None:
                    result = location_data
                    break
            else:
                adderss = iterable_to_string(self.address_components, True)
                logging.error('Ungeocoded localization: %s\n%s' %
                              (adderss, self.url))

                result = normalize_address(self.address_components)
                self._set_ungeocoded()

                return result

        result['latitude'] = round(result['latitude'], 5)
        result['longitude'] = round(result['longitude'], 5)
        result = normalize_address(result)

        r_valid_for = comparable_address(self.address_components)
        g_valid_for = comparable_address(result)

        if r_valid_for != g_valid_for:
            result['valid_for'] = r_valid_for + '|' + g_valid_for
        else:
            result['valid_for'] = r_valid_for

        return result

    def get_missing_components(self):
        """Collect missing address components from reverse geocoding results.
        This method is used to get missing data (which are 'region' and
        'district') for already stored locations. Coordinates floating
        precision is lowered (and thus edited coordinates returned as tuple for
        another reverse geocoding, and stored in cache) if desired components
        are not in the result until everything is collected. If coordinates
        floating precision limit is reached, standard token (taken from config)
        is used to mark these address components as ungeocoded.

        :return dict or tuple

        """
        result = {'completion': True,
                  'latitude': self.address_coordinates['latitude'],
                  'longitude': self.address_coordinates['longitude']}

        for _result in self.geocoding_result['results']:
            for addr_cmp in _result['address_components']:
                cmp_name = addr_cmp['long_name']

                for addr_cmp_type, result_cmp_type in self.missing_cmps_types:
                    if addr_cmp_type in addr_cmp['types']:
                        if result_cmp_type in result:
                            continue

                        result[result_cmp_type] = cmp_name

        coordinates = (self.address_coordinates['latitude'],
                       self.address_coordinates['longitude'])

        if 'region' not in result or 'district' not in result:
            precision = None              # rounding precision
            rounded_coordinates = None    # list of rounded coordinates

            for key, values in self.partial_cache.items():
                if coordinates not in values:
                    continue

                rounded_coordinates = self.partial_cache[key]
                precision = self._precision(rounded_coordinates[-1]) - 1
                break

            if precision is None:
                precision = self._precision(coordinates) - 1

                self.partial_cache[coordinates] = []
                rounded_coordinates = self.partial_cache[coordinates]

            # coordinates floating precision limit reached
            if precision == 1:
                for _, result_cmp_type in self.missing_cmps_types:
                    if result_cmp_type in result:
                        if result[result_cmp_type] is None:
                            result[result_cmp_type] = ungeocoded_component
                    else:
                        result[result_cmp_type] = ungeocoded_component

                self._clear_from_cache(coordinates, result)
                result = normalize_address(result)

                return result

            lat = round(self.address_coordinates['latitude'], precision)
            lng = round(self.address_coordinates['longitude'], precision)
            rounded_coordinates.append((lat, lng))

            return (lat, lng)

        self._clear_from_cache(coordinates, result)
        result = normalize_address(result)

        return result

    @property
    def geocoding_result(self):
        return self._result

    @geocoding_result.setter
    def geocoding_result(self, response):
        """Set geocoding_result, i.e. check if response is a JSON and status is
        OK, otherwise a re-geocoding is needed

        :argument response: response to GET URL request
        :type response: `requests.models.Response`

        :return dict or None

        """
        g_json = response.json()
        g_json_status = g_json['status']

        if g_json_status != 'OK':
            if g_json_status != 'OVER_QUERY_LIMIT':
                logging.error(g_json_status + ' - ' + response.url)

            if g_json_status == 'ZERO_RESULTS':
                self._result = 0
            else:
                self._result = None
        else:
            self._result = g_json

    @property
    def address_components(self):
        return self._addr_cmps

    @address_components.setter
    def address_components(self, addr_cmps):
        """Map addr_cmps tuple to a dictionary

        :argument addr_cmps: address parts
        :type addr_cmps: tuple

        :return dict

        """
        self._addr_cmps = OrderedDict()

        self._addr_cmps['district'] = addr_cmps[0]
        self._addr_cmps['city'] = addr_cmps[1]
        self._addr_cmps['locality'] = addr_cmps[2]

    @property
    def address_coordinates(self):
        return self._addr_crdnts

    @address_coordinates.setter
    def address_coordinates(self, addr_crdnts):
        """Map _addr_crdnts tuple to a dictionary

        :argument addr_crdnts: address coordinates
        :type addr_crdnts: tuple

        :return dict

        """
        self._addr_crdnts = {'latitude': addr_crdnts[0],
                             'longitude': addr_crdnts[1]}
