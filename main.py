import json
import requests

FOREX_FACTORY_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"


def get_calendar_data():
    print("Connecting to ForexFactory calendar...")

    response = requests.get(
        FOREX_FACTORY_URL,
        timeout=15
    )

    response.raise_for_status()

    calendar_data = response.json()

    return calendar_data


def main():
    try:
        calendar_data = get_calendar_data()

        print("Connection successful!")
        print(f"Events received: {len(calendar_data)}")

        print("\nFirst event:")
        print(json.dumps(calendar_data[0], indent=2))

    except requests.RequestException as error:
        print(f"Connection error: {error}")

    except ValueError as error:
        print(f"JSON error: {error}")

    except IndexError:
        print("No calendar events were received.")


if __name__ == "__main__":
    main()
