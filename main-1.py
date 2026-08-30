from fastapi import FastAPI, Response
from scraper import get_clean_calendar_data

app = FastAPI()


@app.get("/")
def home():
    return {
        "status": "SmartFX Forex Calendar Service is running"
    }


@app.get("/calendar")
def get_calendar(response: Response):
    try:
        calendar_data, was_cached = get_clean_calendar_data()

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
