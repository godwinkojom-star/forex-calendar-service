import time
from datetime import datetime, timezone
import requests

# The free ForexFactory JSON feed only reliably provides "this week"
# data. "nextweek"/"lastweek" URLs following the same naming pattern
# do not exist on this free endpoint (confirmed: they 404) - a paid or
# different data source would be needed for that, which we're avoiding
# for now to keep this project free.
FOREX_FACTORY_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

# How long a cached result stays valid before we try fetching fresh data
# again. 25 minutes was chosen to go easy on ForexFactory's server while
# still being fresh enough for "event coming up" style logic. If you later
# need faster reaction to released ("actual") values, lower this.
CACHE_TTL_SECONDS = 25 * 60  # 25 minutes

# In-memory cache. Lives only as long as this process is running - it
# resets on every redeploy/restart, which is fine for this use case.
_cache = {
    "data": None,        # last successful clean_calendar_data list
    "fetched_at": None,  # unix timestamp of when it was fetched
}


def _cache_is_fresh():
    if _cache["data"] is None or _cache["fetched_at"] is None:
        return False
    return (time.time() - _cache["fetched_at"]) < CACHE_TTL_SECONDS


def get_raw_calendar_data():
    """
    Download the raw weekly calendar data.
    """

    response = requests.get(
        FOREX_FACTORY_URL,
        timeout=15
    )

    response.raise_for_status()

    return response.json()


def _to_utc_iso_string(date_str):
    """
    Take ForexFactory's offset-aware date string (e.g.
    "2026-09-04T08:30:00-04:00") and convert it to a plain UTC ISO
    string (e.g. "2026-09-04T12:30:00Z"). This lets the bot compare
    event times directly against UTC "now" with zero offset math of
    its own - no matter what timezone the bot's server runs in.

    Returns None if date_str is missing or can't be parsed, so a bad
    date never crashes the whole request - it just leaves date_utc
    empty for that one event.
    """

    if not date_str:
        return None

    try:
        parsed = datetime.fromisoformat(date_str)

        if parsed.tzinfo is None:
            # No offset in the string at all (a "naive" datetime).
            # Do NOT call .astimezone() here - on a naive datetime that
            # silently assumes the *server's local system timezone*,
            # which would produce a different (wrong) date_utc depending
            # on where this happens to be deployed. Fail safe instead,
            # same as we do for missing/garbage dates.
            return None

        utc_dt = parsed.astimezone(timezone.utc)
        # Replace "+00:00" with "Z", the more common UTC suffix.
        return utc_dt.isoformat().replace("+00:00", "Z")
    except (ValueError, TypeError):
        return None


def clean_calendar_event(event):
    """
    Convert one raw ForexFactory event into
    our own clean JSON structure.
    """

    original_date = event.get("date")

    return {
        "date": original_date,
        "date_utc": _to_utc_iso_string(original_date),
        "currency": event.get("country"),
        "impact": event.get("impact"),
        "event": event.get("title"),
        "actual": event.get("actual"),
        "forecast": event.get("forecast"),
        "previous": event.get("previous")
    }


def get_clean_calendar_data():
    """
    Return clean calendar data, using a 25-minute cache.

    Behavior:
    - If the cache is fresh (< 25 min old), return it without hitting
      ForexFactory at all.
    - If the cache is stale (or empty), try to fetch fresh data.
        - On success: update the cache and return the fresh data.
        - On failure: if we have ANY previously cached data (even if
          stale), return that instead of failing outright, so a single
          ForexFactory hiccup doesn't take the whole API down. The
          caller (main.py) is told whether the data was fresh or cached
          via the "was_cached" flag.
    Raises the original exception only if there is no cached data at
    all to fall back on (e.g. very first request ever fails).
    """

    if _cache_is_fresh():
        return _cache["data"], True

    try:
        raw_calendar_data = get_raw_calendar_data()

        clean_calendar_data = []
        for event in raw_calendar_data:
            clean_event = clean_calendar_event(event)
            clean_calendar_data.append(clean_event)

        _cache["data"] = clean_calendar_data
        _cache["fetched_at"] = time.time()

        return clean_calendar_data, False

    except Exception:
        if _cache["data"] is not None:
            # Fetch failed, but we have older data - better than nothing.
            return _cache["data"], True
        # No fresh data and no cached fallback - nothing we can do.
        raise
