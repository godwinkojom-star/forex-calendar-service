from fastapi import FastAPI, Response
from scraper import get_clean_calendar_data

app = FastAPI()


@app.get("/")
def home():
    return {
        "status": "SmartFX Forex Calendar Service is running"
    }


def _matches_filter(event_value, allowed_values):
    """
    Case-insensitive membership check. `allowed_values` is a set of
    lowercase strings, or None/empty meaning "no filter, allow all".
    """
    if not allowed_values:
        return True
    if event_value is None:
        return False
    return event_value.strip().lower() in allowed_values


def _parse_filter_param(raw_value):
    """
    Turn a comma-separated query param like "USD,EUR" into a lowercase
    set {"usd", "eur"}. Returns None if raw_value is empty/not given.
    """
    if not raw_value:
        return None
    return {
        piece.strip().lower()
        for piece in raw_value.split(",")
        if piece.strip()
    }


@app.get("/calendar")
def get_calendar(
    response: Response,
    impact: str = None,
    currency: str = None,
):
    """
    Query params:
    - impact: optional, comma-separated e.g. "high" or "high,medium"
    - currency: optional, comma-separated e.g. "USD" or "USD,EUR"

    Only returns "this week" data - that's the only window the free
    ForexFactory feed provides.
    """

    try:
        calendar_data, was_cached = get_clean_calendar_data()

        impact_filter = _parse_filter_param(impact)
        currency_filter = _parse_filter_param(currency)

        if impact_filter or currency_filter:
            calendar_data = [
                event for event in calendar_data
                if _matches_filter(event.get("impact"), impact_filter)
                and _matches_filter(event.get("currency"), currency_filter)
            ]

        return {
            "success": True,
            "cached": was_cached,
            "total_events": len(calendar_data),
            "events": calendar_data
        }

    except Exception as error:
        # No fresh data AND no cached fallback available - this is a
        # real failure the bot needs to notice, so we return a proper
        # error status instead of a plain 200. Anything checking only
        # the HTTP status code (not the "success" field) will now
        # correctly see this as a failure.
        response.status_code = 502
        return {
            "success": False,
            "error": str(error)
        }
