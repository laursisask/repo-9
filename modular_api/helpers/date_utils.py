from datetime import datetime


def convert_datetime_to_human_readable(datetime_object):
    if isinstance(datetime_object, datetime):
        return datetime_object.strftime("%d.%m.%Y %H:%M:%S")
    return datetime_object


def utc_time_now():
    """
    Uses for datetime compatibility between saas & onprem mode
    """
    return datetime.utcnow().replace(microsecond=0)
