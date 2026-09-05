"""Birth time -> Julian Day, resolved through the historical timezone.

The rule this module exists to enforce: a chart must use the UTC offset that was
in force at that place on that date, not the offset in force today. India is the
classic trap (Howrah Mean Time +5:53:20 before 1906, Madras Mean Time +5:21:10,
a wartime +6:30 in 1942-45, IST only later), but shifting DST rules affect most
of the world. We resolve coordinates to an IANA zone and let the tz database
answer the historical question.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import swisseph as swe
from timezonefinder import TimezoneFinder

_tf = TimezoneFinder()


def timezone_for(lat: float, lon: float) -> str:
    """IANA zone name for a coordinate pair.

    Falls back to a whole-hour zone derived from longitude for ocean points and
    other gaps in the shapefile, so a chart never fails outright.
    """
    name = _tf.timezone_at(lat=lat, lng=lon)
    if name:
        return name
    name = _tf.certain_timezone_at(lat=lat, lng=lon)
    if name:
        return name
    offset_hours = round(lon / 15.0)
    # Etc/GMT zones use the opposite sign convention to what you would expect.
    return f"Etc/GMT{-offset_hours:+d}"


def utc_offset_at(lat: float, lon: float, local_dt: datetime,
                  tz_name: str | None = None) -> tuple[float, str, str]:
    """Return (offset_hours, tz_name, abbreviation) for a *naive* local datetime.

    offset_hours can be fractional -- historical zones such as +5:53:20 are not
    whole hours, and rounding them would move the ascendant by degrees.
    """
    tz_name = tz_name or timezone_for(lat, lon)
    try:
        tz = ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError):
        tz = ZoneInfo("UTC")
        tz_name = "UTC"
    aware = local_dt.replace(tzinfo=tz)
    off = aware.utcoffset() or timedelta(0)
    return off.total_seconds() / 3600.0, tz_name, aware.tzname() or ""


def lmt_offset(lon: float) -> float:
    """Local Mean Time offset in hours for a longitude. 15 degrees == 1 hour."""
    return lon / 15.0


# Abbreviations the tz database uses for pre-standard *city* mean times.
# Asia/Kolkata for example reports HMT (Howrah) and MMT (Madras) -- both are the
# mean time of one particular city, not of the whole zone.
_MEAN_TIME_ABBREVS = {
    "LMT", "HMT", "MMT", "BMT", "PMT", "RMT", "AMT", "CMT",
    "SMT", "DMT", "IMT", "JMT", "KMT", "TMT", "FMT", "NMT", "SJMT",
}


def is_pre_standard_time(abbrev: str, offset_hours: float) -> bool:
    """Was this zone still on a local mean time at that moment?

    Two signals. An offset that is not a whole multiple of 15 minutes can only
    be a mean time -- every real standard zone is a multiple of 15 minutes. And
    the tz database labels these periods with mean-time abbreviations.
    """
    seconds = round(offset_hours * 3600)
    if seconds % 900 != 0:
        return True
    return abbrev.upper() in _MEAN_TIME_ABBREVS


def local_to_utc(local_dt: datetime, lat: float, lon: float,
                 tz_name: str | None = None,
                 override_offset_hours: float | None = None,
                 time_standard: str = "auto",
                 ) -> tuple[datetime, float, str, str, str, list[str]]:
    """Convert naive local birth time to UTC.

    Returns (utc, offset_hours, tz_name, abbrev, standard_used, notes).

    ``time_standard``:
      ``zone`` always trusts the tz database;
      ``lmt``  always uses Local Mean Time for the birth longitude;
      ``auto`` (default) uses the zone, except where the tz database is still
      reporting a *city* mean time for that date -- in which case the clock on
      the wall was the birth town's own mean time, and using another city's
      shifts the lagna. For Gandhi's Porbandar birth in 1869 that difference is
      1h15m, enough to move the ascendant a whole sign.

    ``override_offset_hours`` pins a known offset (say from a birth record) and
    wins outright.
    """
    notes: list[str] = []
    tz_name = tz_name or timezone_for(lat, lon)

    if override_offset_hours is not None:
        utc_dt = local_dt - timedelta(hours=override_offset_hours)
        return (utc_dt.replace(tzinfo=timezone.utc), override_offset_hours,
                tz_name, "manual", "manual", notes)

    zone_offset, tz_name, abbrev = utc_offset_at(lat, lon, local_dt, tz_name)

    use_lmt = time_standard == "lmt"
    if time_standard == "auto" and is_pre_standard_time(abbrev, zone_offset):
        use_lmt = True
        notes.append(
            f"This date predates standard time here -- the tz database still "
            f"reports {abbrev or 'a local mean time'}, which is one particular "
            f"city's mean time. Used Local Mean Time for the birth longitude "
            f"instead, the clock that would actually have been kept locally.")

    if use_lmt:
        offset = lmt_offset(lon)
        utc_dt = local_dt - timedelta(hours=offset)
        return (utc_dt.replace(tzinfo=timezone.utc), offset, tz_name,
                "LMT", "lmt", notes)

    utc_dt = local_dt - timedelta(hours=zone_offset)
    return (utc_dt.replace(tzinfo=timezone.utc), zone_offset, tz_name,
            abbrev, "zone", notes)


def julian_day(utc_dt: datetime) -> float:
    """Julian Day (UT) for an aware UTC datetime."""
    hour = (utc_dt.hour + utc_dt.minute / 60.0
            + (utc_dt.second + utc_dt.microsecond / 1e6) / 3600.0)
    return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour, swe.GREG_CAL)


def jd_to_utc(jd: float) -> datetime:
    """Inverse of :func:`julian_day`."""
    y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
    total_seconds = h * 3600.0
    hh = int(total_seconds // 3600)
    mm = int((total_seconds % 3600) // 60)
    ss_f = total_seconds % 60
    ss = int(ss_f)
    us = int(round((ss_f - ss) * 1e6))
    if us >= 1_000_000:      # guard against float dust rounding to a full second
        us -= 1_000_000
        ss += 1
    base = datetime(y, m, d, tzinfo=timezone.utc)
    return base + timedelta(hours=hh, minutes=mm, seconds=ss, microseconds=us)


def jd_to_local(jd: float, offset_hours: float) -> datetime:
    """Julian Day -> naive local wall-clock time at a fixed offset."""
    return (jd_to_utc(jd) + timedelta(hours=offset_hours)).replace(tzinfo=None)


@dataclass(frozen=True)
class BirthMoment:
    """Everything downstream needs to place a chart in space and time."""
    jd_ut: float
    utc: datetime
    local: datetime
    latitude: float
    longitude: float
    tz_name: str
    utc_offset_hours: float
    tz_abbrev: str
    time_known: bool
    time_standard: str = "zone"
    notes: tuple[str, ...] = ()

    @property
    def offset_label(self) -> str:
        sign = "+" if self.utc_offset_hours >= 0 else "-"
        mag = abs(self.utc_offset_hours)
        h = int(mag)
        m = int(round((mag - h) * 60))
        s = 0
        # Zones such as +5:53:20 need the seconds field to round-trip honestly.
        exact = abs(mag * 3600 - (h * 3600 + m * 60))
        if exact > 1:
            total = int(round(mag * 3600))
            h, rem = divmod(total, 3600)
            m, s = divmod(rem, 60)
        return f"UTC{sign}{h:02d}:{m:02d}" + (f":{s:02d}" if s else "")


def build_moment(date_str: str, time_str: str | None, lat: float, lon: float,
                 tz_name: str | None = None,
                 override_offset_hours: float | None = None,
                 time_standard: str = "auto") -> BirthMoment:
    """Assemble a :class:`BirthMoment` from form input.

    When the birth time is unknown we anchor the day at 12:00 local. Noon keeps
    the Moon's error smallest for a date-only chart (it is never more than about
    +/-6 hours of motion away) and keeps the date stable under any offset.
    """
    time_known = bool(time_str)
    hh, mm, ss = 12, 0, 0
    if time_known:
        parts = [int(p) for p in str(time_str).split(":")]
        hh = parts[0]
        mm = parts[1] if len(parts) > 1 else 0
        ss = parts[2] if len(parts) > 2 else 0

    y, mo, d = [int(p) for p in str(date_str).split("-")]
    local_dt = datetime(y, mo, d, hh, mm, ss)

    utc_dt, offset, tz_name, abbrev, standard, notes = local_to_utc(
        local_dt, lat, lon, tz_name, override_offset_hours, time_standard)

    return BirthMoment(
        jd_ut=julian_day(utc_dt),
        utc=utc_dt,
        local=local_dt,
        latitude=lat,
        longitude=lon,
        tz_name=tz_name,
        utc_offset_hours=offset,
        tz_abbrev=abbrev,
        time_known=time_known,
        time_standard=standard,
        notes=tuple(notes),
    )
