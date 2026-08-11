import os
import requests
import urllib.parse

# --- Config from environment variables ---
BOT_TOKEN = os.environ["8785834969:AAFl8p3k4AvOwU0IvEqzUYD1a5pSObAp2qQ"]
CHAT_ID = os.environ["741974904"]
PSI_THRESHOLD = int(os.environ.get("PSI_THRESHOLD", "100"))

# --- NEA PSI API (data.gov.sg v2 real-time) ---
PSI_URL = "https://api-open.data.gov.sg/v2/real-time/api/psi"

def get_psi_data():
    resp = requests.get(PSI_URL, timeout=10)
    resp.raise_for_status()
    return resp.json()

def check_psi_and_build_message(data):
    # data structure: {"code":0, "data": {"items": [ {...} ] }}
    items = data.get("data", {}).get("items", [])
    if not items:
        return None

    latest = items[-1]  # latest item
    timestamp = latest.get("timestamp", "")

    regions = ["north", "south", "east", "west", "central"]
    alerts = []

    for region in regions:
        psi_val = latest.get("readings", {}).get("psi_twenty_four_hourly", {}).get(region)
        if psi_val is None:
            continue
        if psi_val >= PSI_THRESHOLD:
            alerts.append(f"{region.capitalize()}: {psi_val}")

    if not alerts:
        return None

    header = f"🚨 Haze Alert (24‑hr PSI ≥ {PSI_THRESHOLD})\n"
    body = "\n".join(alerts)
    footer = f"\nTime (SGT): {timestamp}"
    return header + body + footer

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }
    resp = requests.post(url, json=payload, timeout=10)
    resp.raise_for_status()

def main():
    data = get_psi_data()
    message = check_psi_and_build_message(data)
    if message:
        send_telegram_message(message)

if __name__ == "__main__":
    main()
