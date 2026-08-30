import os

from flask import Flask, jsonify
from scraper import get_clean_calendar_data


app = Flask(__name__)


@app.route("/")
def home():
    return jsonify({
        "service": "Forex Calendar Service",
        "status": "online"
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy"
    })


@app.route("/calendar")
def calendar():
    try:
        calendar_data = get_clean_calendar_data()

        return jsonify({
            "success": True,
            "total_events": len(calendar_data),
            "events": calendar_data
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))

    print("Starting Forex Calendar Service...")
    print(f"Listening on port {port}")

    app.run(
        host="0.0.0.0",
        port=port
    )
