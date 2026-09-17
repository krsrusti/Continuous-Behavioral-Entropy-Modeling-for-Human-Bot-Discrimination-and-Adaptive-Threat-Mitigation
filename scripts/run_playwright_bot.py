
"""
run_playwright_bot.py

Playwright-based script bot for TIF data collection.

Flow:
    1. Register a bot experiment with /api/experiment/start
    2. Receive experiment_id + participant_id
    3. Automatically build an experiment-specific login URL
    4. Open the page with Playwright
    5. Fill the login form
    6. Submit the form
    7. Wait for TIF session transmission

Requirements:
    pip install playwright
    playwright install chromium

Run:
    python scripts\run_playwright_bot.py
"""

import json
import time
import urllib.request

from playwright.sync_api import sync_playwright


# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

API = "http://localhost:5000"

PAGE_BASE = "http://localhost:8080/templates/login.html"


# ─────────────────────────────────────────────────────────────────────────────
# HELPER — POST JSON TO FLASK
# ─────────────────────────────────────────────────────────────────────────────

def post(url, data):
    payload = json.dumps(data).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — CREATE EXPERIMENT
# ─────────────────────────────────────────────────────────────────────────────

print("\n[Playwright Bot] Registering experiment...")

try:
    experiment = post(
        f"{API}/api/experiment/start",
        {
            "agent_class": "bot",
            "task_id": "login",
            "probe_enabled": True,
            "notes": "playwright bot"
        }
    )

except Exception as error:
    print("\n[ERROR] Could not connect to Flask API.")
    print("Make sure your Flask backend is running.")
    print(f"Details: {error}")
    raise SystemExit(1)


experiment_id = experiment["experiment_id"]
participant_id = experiment["participant_id"]


print("[Playwright Bot] Experiment ID :", experiment_id)
print("[Playwright Bot] Participant ID:", participant_id)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — BUILD EXPERIMENT-SPECIFIC URL
# ─────────────────────────────────────────────────────────────────────────────

session_url = (
    f"{PAGE_BASE}"
    f"?experiment_id={experiment_id}"
    f"&participant_id={participant_id}"
    f"&probe_enabled=true"
    f"&task_id=login"
)


print("[Playwright Bot] Session URL:")
print(session_url)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — START PLAYWRIGHT
# ─────────────────────────────────────────────────────────────────────────────

with sync_playwright() as playwright:

    print("\n[Playwright Bot] Starting Chromium...")

    browser = playwright.chromium.launch(
        headless=False
    )

    page = browser.new_page()


    # ─────────────────────────────────────────────────────────────────────────
    # STEP 4 — OPEN EXPERIMENT-SPECIFIC PAGE
    # ─────────────────────────────────────────────────────────────────────────

    print("[Playwright Bot] Opening login page...")

    page.goto(
        session_url,
        wait_until="domcontentloaded"
    )


    # Give your telemetry scripts and micro-probes time to initialize.
    time.sleep(3)


    # ─────────────────────────────────────────────────────────────────────────
    # STEP 5 — FILL EMAIL
    # ─────────────────────────────────────────────────────────────────────────

    print("[Playwright Bot] Filling email...")

    page.locator("#email").fill(
        "playwrightbot@test.com"
    )


    # ─────────────────────────────────────────────────────────────────────────
    # STEP 6 — FILL PASSWORD
    # ─────────────────────────────────────────────────────────────────────────

    print("[Playwright Bot] Filling password...")

    page.locator("#password").fill(
        "password123"
    )


    # ─────────────────────────────────────────────────────────────────────────
    # STEP 7 — SUBMIT FORM
    # ─────────────────────────────────────────────────────────────────────────

    print("[Playwright Bot] Submitting login form...")

    page.locator(
        'button[type="submit"]'
    ).click()


    # Give the JavaScript submit handler time to:
    #   1. POST /api/session
    #   2. POST /api/risk
    #   3. finish transmitting telemetry
    time.sleep(3)


    # ─────────────────────────────────────────────────────────────────────────
    # STEP 8 — SHOW RESULT
    # ─────────────────────────────────────────────────────────────────────────

    print("\n[Playwright Bot] Browser interaction completed.")

    print("[Playwright Bot] Experiment ID:", experiment_id)
    print("[Playwright Bot] Waiting for session transmission...")


    # Keep browser open briefly so asynchronous requests can finish.
    time.sleep(2)


    browser.close()


print("\n[Playwright Bot] Browser closed.")
print("[Playwright Bot] Session collection finished.")
