from datetime import datetime

import pytz
from pytz.tzinfo import StaticTzInfo


def jp_tz() -> StaticTzInfo:
    return pytz.timezone("Asia/Tokyo")  # type: ignore


def now_dt() -> datetime:
    return datetime.now(jp_tz())
