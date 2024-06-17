from datetime import datetime, timezone
from dateutil.parser import isoparse


def convert_datetime_to_human_readable(datetime_object) -> str | None:
    # god like method to handle all possible developer errors. God bless that
    # day when this method becomes decommissioned and replaced with some
    # static type checker
    if not datetime_object:
        return
    if isinstance(datetime_object, (int, float)):
        datetime_object = datetime.fromtimestamp(datetime_object)
    elif isinstance(datetime_object, str):
        try:
            datetime_object = datetime.fromisoformat(datetime_object)
        except ValueError:
            datetime_object = isoparse(datetime_object)
    return datetime_object.strftime("%d.%m.%Y %H:%M:%S")


def utc_time_now() -> datetime:
    """
    Uses for datetime compatibility between saas & onprem mode
    """
    return datetime.now(tz=timezone.utc)
