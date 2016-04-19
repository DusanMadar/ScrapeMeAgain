# -*- coding: utf-8 -*-


"""Shared alphanumeric functions"""


from time import time
from datetime import datetime
from unicodedata import normalize


def current_date_time_stamp():
    """Format current date time stamp"""
    return datetime.now().strftime('%Y.%m.%d %H:%M:%S.%f')[:-7]


def date_stamp():
    """Create a date stamp in `YYYY.MM.DD` format

    :returns str

    """
    return datetime.fromtimestamp(time()).strftime('%Y.%m.%d')


def datetime_stamp(string_ts):
    """Create date-time stamp in `DD.MM.YYYY HH:MM:SS` format

    :argument string_ts: date-time stamp
    :type string_ts: str

    :returns datetime object

    """
    return datetime.strptime(string_ts, '%d.%m.%Y %H:%M:%S')


def strip_space(string):
    """Remove spaces from string

    :argument string: target string
    :type string: str

    :returns str

    """
    return string.replace(' ', '')


def string_to_digit(string, output):
    """Convert string to float/int if possible (designed to extract number
    from a price sting, e.g. 250 EUR -> 250)

    :argument string: string to convert
    :type string: str
    :argument output: output type
    :type output: type

    :returns float/int or None

    """
    string = strip_space(string)
    if not string[0].isdigit() and not string[1].isdigit():
        return None

    string_items = []
    for index, item in enumerate(string):
        if item.isdigit():
            string_items.append(item)
        else:
            if item == ',':
                string_items.append('.')

            elif item == ' ' and string[index + 1].isdigit():
                pass

            elif not item.isdigit() and not string[index + 1].isdigit():
                break

    if '.' in string_items and output == int:
        return int(float(''.join(string_items)))

    return output(''.join(string_items))


def string_to_ascii(string):
    """Convert UTF-8 encoded string to ASCII

    :argument string: UTF-8 string
    :type string: str or None

    :returns str or None

    """
    if string is None:
        return

    if isinstance(string, str):
        string = string.decode('utf-8')

    return normalize('NFKD', string).encode('ASCII', 'ignore')


def comparable_string(string):
    """Make comparable string, i.e. a lower-case ASCII string without spaces

    :returns str or None

    """
    if string is None:
        return

    string = string_to_ascii(string)
    string = strip_space(string)
    string = string.lower()

    return string


def handle_dots(string):
    """Handle `.` chars accordingly, i.e. remove if last and add a space after

    :argument string: string to handle dots in
    :type string: str

    :returns str

    """
    if '.' in string:
        if string[-1] == '.':
            string = string[:-1]
        else:
            string = string.replace('.', '. ')

    return string


def handle_dashes(string):
    """Handle `-` chars accordingly, i.e. add spaces around

    :argument string: string to handle dashes in
    :type string: str

    :returns str

    """
    if '-' in string:
        string = string.replace('-', ' - ')

    return string


def float_precision(float_number):
    """Get float decimal precision

    :argument float_number: floating point number
    :type float_number: float

    :returns int

    """
    decimal = str(float_number).split('.')[-1]
    return len(decimal)


def iterable_to_string(iterable, quoted=False):
    """Convert an iterable to string

    :argument iterable:
    :type iterable: tuple, list, dict
    :argument quoted: flag to wrap each iterable item in single quotes
    :type quoted: bool

    :returns str

    """
    if isinstance(iterable, dict):
        iterable = [unicode(i) for i in iterable.values()]
    else:
        iterable = [unicode(i) for i in iterable]

    if quoted:
        iterable = ['\'%s\'' % unicode(i) for i in iterable]

    return ', '.join(iterable)
