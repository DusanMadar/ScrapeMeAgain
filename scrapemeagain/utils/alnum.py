"""Common alphanumeric functions."""


from datetime import datetime


DATE_FORMAT = "%Y.%m.%d"
TIME_FORMAT = "%H:%M:%S"
DATE_TIME_FORMAT = "{d} {t}".format(d=DATE_FORMAT, t=TIME_FORMAT)


def get_current_date():
    """Get a `YYYY.MM.DD` date stamp.

    :returns str
    """
    return datetime.strftime(datetime.now(), DATE_FORMAT)


def get_current_datetime():
    """Get a `YYYY.MM.DD hh:mm:ss` datetime stamp.

    :returns str
    """
    return datetime.strftime(datetime.now(), DATE_TIME_FORMAT)
