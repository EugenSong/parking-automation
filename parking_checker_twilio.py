# parking_checker_discord.py

import asyncio
import json
import os
import requests
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError

# --- CONFIGURATION ---

BASE_URL = "https://parkingattendant.app/policy/mwq14sf04578bekqv3tbte7r3w/spaces/map?level={}"

FLOORS_TO_MONITOR = [2, 3, 4]  # Only alert for floors 2-4
ALL_CHECK_FLOORS   = [2, 3, 4, 5, 6, 7]  # Still check all floors for logging

# Discord webhook configuration
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/1436599795232800849/MKz3TJ8af4JT-q9efTQjlpcIkPF4_tUYUalkmOXJlN_08Ds6PCDkjuC2Q0EvCResn1fN")

# -------------------------

def send_discord_notification(message: str):
    """Send notification to Discord via webhook"""
    payload = {"content": message}
    resp = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if resp.status_code == 204:
        print(f"[{datetime.now()}] Discord notification sent successfully")
    else:
        print(f"[{datetime.now()}] Failed to send Discord notification — status {resp.status_code}, response {resp.text}")

async def fetch_floor_statuses():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        floors = {}
        for floor_num in ALL_CHECK_FLOORS:
            url = BASE_URL.format(floor_num)
            print(f"[{datetime.now()}] Navigating to {url}")
            await page.goto(url, timeout=90000)
            try:
                await page.wait_for_selector("figure.level", timeout=15000)
            except PWTimeoutError:
                print(f"[{datetime.now()}] Timeout waiting for floor {floor_num}")
            await page.wait_for_timeout(5000)

            el = await page.query_selector("figure.level")
            if not el:
                print(f"[{datetime.now()}] Could not find figure.level for floor {floor_num}")
                continue

            lvl_data   = await el.query_selector("h1 data.level")
            floor_val  = await (lvl_data.get_attribute("value") if lvl_data else str(floor_num))
            p_data     = await el.query_selector("p data[value]")
            status_txt = (await p_data.inner_text()).strip() if p_data else "unknown"

            label = f"Floor {floor_val}"
            floors[label] = status_txt

        await browser.close()
        return floors

async def main():
    current = await fetch_floor_statuses()
    print(f"[{datetime.now()}] Current statuses: {current}")

    alerts = []
    for floor_label, status in current.items():
        try:
            floor_num = int(floor_label.split()[1])
        except:
            continue
        if floor_num in FLOORS_TO_MONITOR:
            if " of " in status:
                try:
                    avail_count = int(status.split(" of ")[0])
                except:
                    avail_count = None
                if avail_count and avail_count > 0:
                    alerts.append(f"{floor_label}: {status}")
            elif "available" in status.lower():
                alerts.append(f"{floor_label}: {status}")

    if alerts:
        body = "🚗 Parking openings:\n" + "\n".join(alerts)
        send_discord_notification(body)
        print(f"[{datetime.now()}] Notification sent:\n{body}")
    else:
        print(f"[{datetime.now()}] No openings on monitored floors: {FLOORS_TO_MONITOR}")

if __name__ == "__main__":
    asyncio.run(main())
