import requests

FOREX_FACTORY_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"


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


def get_clean_calendar_data():
    """
    Download calendar data and convert every event
    into our clean structure.
    """

    raw_calendar_data = get_raw_calendar_data()

    clean_calendar_data = []

    for event in raw_calendar_data:
        clean_event = clean_calendar_event(event)
        clean_calendar_data.append(clean_event)

    return clean_calendar_data
