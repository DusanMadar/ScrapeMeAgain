# -*- coding: utf-8 -*-


"""Manage Slovak addresses (district, city, locality) cleanup and comparison"""


import re
import logging

from configparser import get_ungeocoded_coordinate
from alphanumericker import (string_to_ascii, comparable_string,
                             handle_dots, handle_dashes)


#:
ungeocoded_coordinate = get_ungeocoded_coordinate()

#: meaningless address parts
FORBIDDEN_PARTS = ('obec', 'ulica', 'ul.', 'ul')

#: regex patterns
digits_pattern = re.compile(r'\d')
nam_pattern = re.compile(ur'n[a,á]m(\.|\s|\Z)', re.IGNORECASE | re.UNICODE)
leading_zero_pattern = re.compile(r'\b0+[1-9]*$')
digit_with_str_pattern = re.compile(r'\d+\/?[aA-zZ]\b')
roman_numeral_pattern = re.compile(r'\b(XC|XL|L?X{0,3})'
                                   '(IX|IV|V?I{0,3})$', re.IGNORECASE)


class Address_cleanup():
    def __call__(self, address):
        """Run all procedures and helper methods to cleanup the address.
        Address is edited only to be geocoding compatible.

        Approved combinations:
             - district, city, locality
             - district, city
             -           city, locality
             -           city
        All other combinations are considered as ambiguous addresses.


        :argument address: address
        :type address: dict

        :returns dict

        """
        self.address = normalize_address(address)

        try:
            self._ensure_city()

            self.city = comparable_string(self.address['city'])
            if 'locality' in self.address:
                self.locality = comparable_string(self.address['locality'])
            else:
                return

            self._manage_short_locality()
            self._manage_forbidden_parts()

            self._manage_square_abbreviation()
            self._manage_street_number()
            self._locality_cleanup()

        except AssertionError:
            pass
        else:
            return self.address

    def _asert(self, condition, remove_items=[], set_coordinates=False):
        """Test the condition, remove items or set coordinates if test fails

        :argument condition: test condition
        :type condition: bool
        :argument remove_items: list of item to remove from self.address
        :type remove_items: list
        :argument set_coordinates: flag if set `special` coordinates
        :type set_coordinates: bool

        """
        try:
            assert condition
        except AssertionError:
            if remove_items:
                for key in remove_items:
                    del self.address[key]

            if set_coordinates:
                # special coordinates are used for ambiguous addresses
                self.address['lat'] = ungeocoded_coordinate
                self.address['lng'] = ungeocoded_coordinate

            raise

    def _ensure_city(self):
        """Ensure that city is always present in the address components"""
        if 'city' not in self.address:
            # often if city is not present locality is a city in fact
            cond1 = 'locality' in self.address
            cond2 = 'district' in self.address
            self._asert(cond1 and cond2, set_coordinates=True)

            self.address['city'] = self.address['locality']
            del self.address['locality']

            msg = 'Replacing city with locality: %s' % str(self.address)
            logging.debug(msg)

    def _manage_square_abbreviation(self):
        """Replace square abbreviation, i.e. nam -> namestie"""
        if 'nam' in self.locality:
            self.address['locality'] = nam_pattern.sub(
                                       'Namestie', self.address['locality'])

            self.locality = comparable_string(self.address['locality'])

    def _manage_street_number(self):
        """Manage street numbers - leading zeroes and chars after numbers"""
        if digits_pattern.search(self.locality):
            num = leading_zero_pattern.search(self.address['locality'])
            if num is not None:
                num = num.group().replace('0', '')

                self.address['locality'] = leading_zero_pattern.sub(
                                           num, self.address['locality'])

            num = digit_with_str_pattern.search(self.address['locality'])
            if num is not None:
                num = digits_pattern.search(num.group())
                if num is not None:
                    num = num.group()
                    self.address['locality'] = digit_with_str_pattern.sub(
                                               num, self.address['locality'])

            self.locality = comparable_string(self.address['locality'])

    def _manage_short_locality(self):
        """Under 3 char long locality is just nonsense, if not a number"""
        if len(self.locality) <= 3:
            cond = self.locality.isdigit()
            self._asert(cond, remove_items=['locality'])

            if 'district' in self.address:
                district = comparable_string(self.address['district'])

                cond = district != self.city not in self.locality
                self._asert(cond, remove_items=['locality'])

    def _manage_forbidden_parts(self):
        """Replace only stand-alone forbidden locality parts"""
        for forbidden_part in FORBIDDEN_PARTS:
            if forbidden_part in self.locality:
                locality_parts = [part.lower() for part in
                                  self.address['locality'].split()]

                for locality_part in locality_parts:
                    if locality_part != forbidden_part:
                        continue

                    locl = self.address['locality'].lower()
                    locl = locl.replace(forbidden_part, '')
                    locl = locl.strip().title()

                    self.locality = comparable_string(locl)
                    self.address['locality'] = locl
                    break

    def _locality_cleanup(self):
        """Special locality cleanup processing"""
        # city == locality
        self._asert(self.locality != self.city, remove_items=['locality'])

        # Nitra - Badice -> Badice
        if '-' in self.locality:
            for _city in self.address['city'].split():
                _city = string_to_ascii(_city).lower()
                _locality = string_to_ascii(self.address['locality']).lower()

                if _city not in _locality.split():
                    continue

                try:
                    _index = _locality.index('-') + 2
                except ValueError:
                    continue

                self.address['locality'] = self.address['locality'][_index:]
                self.locality = comparable_string(self.address['locality'])

        self.address['locality'] = self.address['locality'].strip().title()
        if self.address['locality'] == '':
            del self.address['locality']

        try:
            district = comparable_string(self.address['district'])
            locality = comparable_string(self.address['locality'])

            if district == locality:
                del self.address['locality']
        except KeyError:
            pass


def normalize_address(addr_cmps):
    """Normalize address to prevent any minor differences in address components
    (e.g. spaces, capitalization, ...), i.e. strip, replace multiple spaces,
    remove meaningless components and titleize.

    :argument addr_cmps: address components
    :type addr_cmps: dict

    :returns dict

    """
    for addr_cmp in addr_cmps.keys():
        if not isinstance(addr_cmps[addr_cmp], (str, unicode)):
            continue

        try:
            addr_cmps[addr_cmp] = handle_dots(addr_cmps[addr_cmp])
            addr_cmps[addr_cmp] = handle_dashes(addr_cmps[addr_cmp])

            if isinstance(addr_cmps[addr_cmp], str):
                addr_cmps[addr_cmp] = addr_cmps[addr_cmp].decode('utf-8')

            value = ' '.join(addr_cmps[addr_cmp].split())
            addr_cmps[addr_cmp] = value.strip().title()

            if addr_cmps[addr_cmp] == '':
                del addr_cmps[addr_cmp]

            roman = roman_numeral_pattern.search(addr_cmps[addr_cmp])
            if roman is not None:
                roman = roman.group()
                if roman == '':
                    continue

                roman = roman.upper()
                value = roman_numeral_pattern.sub(roman, addr_cmps[addr_cmp])

                addr_cmps[addr_cmp] = value
        except KeyError:
            pass

    return addr_cmps


def comparable_address(addr_cmps):
    """Convert address components to a comparable string

    :argument addr_cmps: address components
    :type addr_cmps: tuple or dict

    :returns str

    """
    address = ''

    if isinstance(addr_cmps, dict):
        for addr_cmp in addr_cmps.keys():
            if not isinstance(addr_cmps[addr_cmp], (str, unicode)):
                continue

            try:
                if addr_cmps[addr_cmp] is None:
                    continue

                address += comparable_string(addr_cmps[addr_cmp])
            except KeyError:
                continue

    elif isinstance(addr_cmps, tuple):
        for addr_cmp in addr_cmps:
            if addr_cmp is None:
                continue

            address += comparable_string(addr_cmp)

    else:
        msg = ('Unexpected address components type:\nGot {type}, expected '
               'dict or tuple').format(type=type(addr_cmps).__name__)
        raise TypeError(msg)

    return address
