from fastapi import FastAPI
from scraper import get_clean_calendar_data

app = FastAPI()


@app.get("/")
def home():
    return {
        "status": "SmartFX Forex Calendar Service is running"
    }


@app.get("/calendar")
def get_calendar():
    try:
        calendar_data = get_clean_calendar_data()

        return {
            "success": True,
            "total_events": len(calendar_data),
            "events": calendar_data
        }

    except Exception as error:
        return {
            "success": False,
            "error": str(error)
        }
