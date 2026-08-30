import time
import requests

# ForexFactory publishes separate fixed JSON feeds for each week window.
FOREX_FACTORY_URLS = {
    "this": "https://nfs.faireconomy.media/ff_calendar_thisweek.json",
    "next": "https://nfs.faireconomy.media/ff_calendar_nextweek.json",
    "last": "https://nfs.faireconomy.media/ff_calendar_lastweek.json",
}

VALID_WEEKS = set(FOREX_FACTORY_URLS.keys())

# How long a cached result stays valid before we try fetching fresh data
# again. 25 minutes was chosen to go easy on ForexFactory's server while
# still being fresh enough for "event coming up" style logic. If you later
# need faster reaction to released ("actual") values, lower this.
CACHE_TTL_SECONDS = 25 * 60  # 25 minutes

# In-memory cache, one independent slot per week. Lives only as long as
# this process is running - it resets on every redeploy/restart, which is
# fine for this use case. Each slot: {"data": [...] or None, "fetched_at": ts or None}
_cache = {
    week: {"data": None, "fetched_at": None}
    for week in VALID_WEEKS
}


def _cache_is_fresh(week):
    slot = _cache[week]
    if slot["data"] is None or slot["fetched_at"] is None:
        return False
    return (time.time() - slot["fetched_at"]) < CACHE_TTL_SECONDS


def get_raw_calendar_data(week):
    """
    Download the raw calendar data for the given week
    ("this", "next", or "last").
    """

    url = FOREX_FACTORY_URLS[week]

    response = requests.get(
        url,
        timeout=15
    )

    response.raise_for_status()

    return response.json()


def clean_calendar_event(event):
    """
    Convert one raw ForexFactory event into
    our own clean JSON structure.
    """

    return {
        "date": event.get("date"),
        "currency": event.get("country"),
        "impact": event.get("impact"),
        "event": event.get("title"),
        "actual": event.get("actual"),
        "forecast": event.get("forecast"),
        "previous": event.get("previous")
    }


def get_clean_calendar_data(week="this"):
    """
    Return clean calendar data for the given week, using a 25-minute
    cache. Each week ("this", "next", "last") has its own independent
    cache slot, so requesting "next" week never evicts "this" week's
    cached data.

    Behavior:
    - If that week's cache is fresh (< 25 min old), return it without
      hitting ForexFactory at all.
    - If the cache is stale (or empty), try to fetch fresh data.
        - On success: update that week's cache and return the fresh data.
        - On failure: if we have ANY previously cached data for that
          week (even if stale), return that instead of failing outright,
          so a single ForexFactory hiccup doesn't take the whole API
          down. The caller (main.py) is told whether the data was
          fresh or cached via the "was_cached" flag.
    Raises the original exception only if there is no cached data at
    all for that week to fall back on (e.g. very first request for
    that week fails).

    Raises ValueError if `week` isn't one of "this", "next", "last".
    """

    if week not in VALID_WEEKS:
        raise ValueError(
            f"Invalid week '{week}'. Must be one of: {sorted(VALID_WEEKS)}"
        )

    if _cache_is_fresh(week):
        return _cache[week]["data"], True

    try:
        raw_calendar_data = get_raw_calendar_data(week)

        clean_calendar_data = []
        for event in raw_calendar_data:
            clean_event = clean_calendar_event(event)
            clean_calendar_data.append(clean_event)

        _cache[week]["data"] = clean_calendar_data
        _cache[week]["fetched_at"] = time.time()

        return clean_calendar_data, False

    except Exception:
        if _cache[week]["data"] is not None:
            # Fetch failed, but we have older data for this week -
            # better than nothing.
            return _cache[week]["data"], True
        # No fresh data and no cached fallback for this week -
        # nothing we can do.
        raise
