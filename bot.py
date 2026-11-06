import os
import time
import requests
from collections import Counter

BASE_URL = "https://api.oktrading.io:8443"

EMAIL = os.getenv("OKTRADING_EMAIL")
PASSWORD = os.getenv("OKTRADING_PASSWORD")

if not EMAIL or not PASSWORD:
    raise RuntimeError(
        "Set OKTRADING_EMAIL and OKTRADING_PASSWORD "
        "as environment variables before running."
    )

session = requests.Session()
session.headers.update({
    "Origin": "https://www.oktrading.io",
    "Referer": "https://www.oktrading.io/",
    "Content-Type": "application/json"
})


def login():
    response = session.post(
        f"{BASE_URL}/frame/login",
        json={"login": EMAIL, "password": PASSWORD},
        timeout=20
    )
    response.raise_for_status()
    result = response.json()

    token = result.get("data", {}).get("token")
    if not token:
        raise RuntimeError("Login failed. Check your credentials.")

    session.headers["Authorization"] = f"Bearer {token}"
    print("Login successful.")


def get_history():
    response = session.post(
        f"{BASE_URL}/api/eth/pageRecordEth",
        json={"pageNum": 1, "pageSize": 100, "type": 1},
        timeout=20
    )
    response.raise_for_status()
    result = response.json()

    if result.get("state") == 301 or str(result.get("msg")) == "10004":
        login()
        response = session.post(
            f"{BASE_URL}/api/eth/pageRecordEth",
            json={"pageNum": 1, "pageSize": 100, "type": 1},
            timeout=20
        )
        response.raise_for_status()
        result = response.json()

    records = result.get("data", {}).get("records", [])

if records:
    print("RECORD FIELDS:", list(records[0].keys()))

colours = []

    for record in records:
        if record.get("recordGreen"):
            colours.append("GREEN")
        elif record.get("recordRed"):
            colours.append("RED")

    return colours


def estimate_next(colours):
    if len(colours) < 20:
        print("Not enough history yet to estimate.")
        return

    recent = colours[:50]
    counts = Counter(recent)
    total = len(recent)

    green_pct = counts["GREEN"] / total * 100
    red_pct = counts["RED"] / total * 100

    print(f"Recent sample: {total} rounds")
    print(f"GREEN frequency: {green_pct:.1f}%")
    print(f"RED frequency:   {red_pct:.1f}%")

    if green_pct > red_pct:
        print("Statistical estimate: GREEN")
    elif red_pct > green_pct:
        print("Statistical estimate: RED")
    else:
        print("Statistical estimate: NO CLEAR EDGE")

    print("This estimate does not guarantee the next result.")


def main():
    login()

    while True:
        try:
            colours = get_history()

            if colours:
                print("\nLatest recorded colour:", colours[0])
                estimate_next(colours)
            else:
                print("No GREEN/RED history returned.")

        except Exception as error:
            print("Request issue:", error)

        print("\nChecking again in 60 seconds...")
        time.sleep(60)


if __name__ == "__main__":
    main()
