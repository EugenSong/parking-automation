# parking_checker_discord.py

import asyncio
import json
import os
import requests
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError

# --- CONFIGURATION ---

PARKING_WEBSITE_URL = "https://parkingattendant.app/policy/mwq14sf04578bekqv3tbte7r3w/spaces/map?level={}"

PREFERRED_FLOORS_TO_MONITOR = [2, 3, 4]
ALL_FLOORS_TO_CHECK = [2, 3, 4, 5, 6, 7]

# Discord webhook configuration (loaded from environment variable)
discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

if not discord_webhook_url:
    raise ValueError("DISCORD_WEBHOOK_URL environment variable is not set")

# -------------------------

def send_notification_to_discord(notification_message: str):
    """Send notification to Discord via webhook"""
    message_payload = {"content": notification_message}
    response = requests.post(discord_webhook_url, json=message_payload)

    if response.status_code == 204:
        print(f"[{datetime.now()}] Discord notification sent successfully")
    else:
        print(f"[{datetime.now()}] Failed to send Discord notification — status {response.status_code}, response {response.text}")

async def scrape_parking_availability_for_all_floors():
    """Scrape the parking website and return availability status for each floor"""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        parking_page = await browser.new_page()
        floor_availability_statuses = {}

        for floor_number in ALL_FLOORS_TO_CHECK:
            floor_url = PARKING_WEBSITE_URL.format(floor_number)
            print(f"[{datetime.now()}] Navigating to {floor_url}")

            await parking_page.goto(floor_url, timeout=90000)

            try:
                await parking_page.wait_for_selector("figure.level", timeout=15000)
            except PWTimeoutError:
                print(f"[{datetime.now()}] Timeout waiting for floor {floor_number}")

            await parking_page.wait_for_timeout(5000)

            floor_container = await parking_page.query_selector("figure.level")
            if not floor_container:
                print(f"[{datetime.now()}] Could not find parking data for floor {floor_number}")
                continue

            floor_level_element = await floor_container.query_selector("h1 data.level")
            floor_value = await (floor_level_element.get_attribute("value") if floor_level_element else str(floor_number))

            availability_data_element = await floor_container.query_selector("p data[value]")
            availability_status_text = (await availability_data_element.inner_text()).strip() if availability_data_element else "unknown"

            floor_label = f"Floor {floor_value}"
            floor_availability_statuses[floor_label] = availability_status_text

        await browser.close()
        return floor_availability_statuses

def extract_available_spot_count_from_status(availability_status: str) -> int:
    """Parse the availability status text to extract the number of available spots"""
    if " of " not in availability_status:
        return 0

    try:
        available_spots = int(availability_status.split(" of ")[0])
        return available_spots
    except ValueError:
        return 0


def build_parking_alerts_for_preferred_floors(all_floor_statuses: dict) -> list:
    """Check preferred floors and build alert messages for any available spots"""
    parking_alerts = []

    for floor_label, availability_status in all_floor_statuses.items():
        try:
            floor_number = int(floor_label.split()[1])
        except (IndexError, ValueError):
            continue

        if floor_number not in PREFERRED_FLOORS_TO_MONITOR:
            continue

        available_spot_count = extract_available_spot_count_from_status(availability_status)

        if available_spot_count > 0:
            parking_alerts.append(f"{floor_label}: {availability_status}")

    return parking_alerts


async def check_parking_and_notify():
    """Main workflow: scrape parking data, check for availability, and send notifications"""
    all_floor_statuses = await scrape_parking_availability_for_all_floors()
    print(f"[{datetime.now()}] Current statuses: {all_floor_statuses}")

    parking_alerts = build_parking_alerts_for_preferred_floors(all_floor_statuses)

    if parking_alerts:
        notification_message = "🚗 Parking openings:\n" + "\n".join(parking_alerts)
    else:
        notification_message = "❌ No spots available on floors 2-4"

    send_notification_to_discord(notification_message)
    print(f"[{datetime.now()}] Notification sent:\n{notification_message}")

if __name__ == "__main__":
    asyncio.run(check_parking_and_notify())
