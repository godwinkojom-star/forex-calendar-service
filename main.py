import json
from scraper import get_clean_calendar_data


def main():
    try:
        print("Downloading ForexFactory calendar data...")

        calendar_data = get_clean_calendar_data()

        print("Calendar data received successfully!")
        print(f"Total events: {len(calendar_data)}")

        print("\nFirst clean event:")

        if calendar_data:
            print(
                json.dumps(
                    calendar_data[0],
                    indent=2
                )
            )
        else:
            print("No events were received.")

    except Exception as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()
