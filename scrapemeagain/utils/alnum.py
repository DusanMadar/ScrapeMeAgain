"""Common alphanumeric functions."""


from datetime import datetime


def get_current_date():
    """Get a `YYYY.MM.DD` date stamp.

    :returns str
    """
    return datetime.strftime(datetime.now(), '%Y.%m.%d')


def get_current_datetime():
    """Get a `YYYY.MM.DD hh:mm:ss` datetime stamp.

    :returns str
    """
    return datetime.strftime(datetime.now(), '%Y.%m.%d %H:%M:%S')
