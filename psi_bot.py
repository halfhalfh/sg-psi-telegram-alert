import os
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
PSI_THRESHOLD = int(os.environ.get("PSI_THRESHOLD", "100"))

PSI_URL = "https://api.data.gov.sg/v1/environment/psi"


def get_psi_data():
    resp = requests.get(PSI_URL, timeout=10)
    resp.raise_for_status()
    return resp.json()


def check_psi_and_build_message(data):
    items = data.get("items", [])
    if not items:
        return None

    latest = items[-1]
    timestamp = latest.get("timestamp", "")

    readings = latest.get("readings", {})
    overall_psi = (
        readings.get("psi_twenty_four_hourly", {}).get("national")
        or readings.get("psi_twenty_four_hourly", {}).get("overall")  # fallback
    )

    regions = ["north", "south", "east", "west", "central"]
    alerts = []

    for region in regions:
        psi_val = (
            readings
            .get("psi_twenty_four_hourly", {})
            .get(region)
        )
        if psi_val is None:
            continue
        if psi_val >= PSI_THRESHOLD:
            alerts.append(f"{region.capitalize()}: {psi_val}")

    if not alerts:
        return None

    header = f"🚨 Haze Alert (24-hr PSI ≥ {PSI_THRESHOLD})\n"
    if overall_psi is not None:
        header += f"Overall (24-hr PSI): {overall_psi}\n"

    body = "\n".join(alerts)
    footer = f"\nTime (SGT): {timestamp}"
    return header + body + footer


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
    }
    resp = requests.post(url, json=payload, timeout=10)
    resp.raise_for_status()


def main():
    data = get_psi_data()
    message = check_psi_and_build_message(data)
    if message:
        send_telegram_message(message)
    else:
        print("No region above threshold. No message sent.")


if __name__ == "__main__":
    main()
