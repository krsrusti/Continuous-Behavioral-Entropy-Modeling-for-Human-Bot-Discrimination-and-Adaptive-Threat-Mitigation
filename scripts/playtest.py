
"""
playwright_bot_variant.py

A second script-bot variant for TIF testing.

Uses:
    POST /api/experiment/start

The backend creates:
    - experiment_id
    - participant_id
    - probe_enabled

The script then automatically builds an experiment-specific URL.

Run:
    python scripts/bot/playwright_bot_variant.py

Requirements:
    pip install playwright
    python -m playwright install chromium
"""

import json
import time
import random
import urllib.request

from playwright.sync_api import sync_playwright


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

API = "http://localhost:5000"
PAGE_BASE = "http://localhost:8080/templates"

TASK_ID = "login"
PROBE_ENABLED = True


# ─────────────────────────────────────────────────────────────────────────────
# Backend helpers
# ─────────────────────────────────────────────────────────────────────────────

def post(url, data):
    payload = json.dumps(data).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def get(url):
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — Create experiment
# ─────────────────────────────────────────────────────────────────────────────

print("\n[Playwright Bot] Registering experiment...")

try:
    experiment = post(
        f"{API}/api/experiment/start",
        {
            "agent_class": "bot",
            "task_id": TASK_ID,
            "probe_enabled": PROBE_ENABLED,
            "notes": "playwright bot variant 2"
        }
    )

except Exception as e:
    print("[ERROR] Could not create experiment.")
    print(e)
    print("Make sure Flask is running.")
    raise SystemExit(1)


experiment_id = experiment["experiment_id"]
participant_id = experiment["participant_id"]


print(f"[Playwright Bot] Experiment ID : {experiment_id}")
print(f"[Playwright Bot] Participant ID: {participant_id}")


# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — Build experiment-specific URL
# ─────────────────────────────────────────────────────────────────────────────

session_url = (
    f"{PAGE_BASE}/login.html"
    f"?experiment_id={experiment_id}"
    f"&participant_id={participant_id}"
    f"&probe_enabled={str(PROBE_ENABLED).lower()}"
    f"&task_id={TASK_ID}"
)

print(f"[Playwright Bot] Session URL: {session_url}")


# ─────────────────────────────────────────────────────────────────────────────
# Step 3 — Run Playwright bot
# ─────────────────────────────────────────────────────────────────────────────

with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=False
    )

    page = browser.new_page()

    print("[Playwright Bot] Opening page...")
    page.goto(session_url)

    # Give the telemetry/probe scripts time to initialise.
    page.wait_for_timeout(3000)

    # -------------------------------------------------------------------------
    # Different interaction pattern from the original instant bot
    # -------------------------------------------------------------------------

    print("[Playwright Bot] Locating email field...")

    email = page.locator("#email")

    email.wait_for()

    # Small deterministic automation pause.
    page.wait_for_timeout(500)

    email.click()

    page.wait_for_timeout(300)

    email.fill("playwright@test.com")

    # -------------------------------------------------------------------------
    # Password
    # -------------------------------------------------------------------------

    print("[Playwright Bot] Locating password field...")

    password = page.locator("#password")

    password.wait_for()

    page.wait_for_timeout(700)

    password.click()

    page.wait_for_timeout(250)

    password.fill("password123")

    # -------------------------------------------------------------------------
    # Small variable pause before submit
    # -------------------------------------------------------------------------

    page.wait_for_timeout(
        random.randint(500, 1200)
    )

    print("[Playwright Bot] Submitting form...")

    submit_button = page.locator(
        "button[type='submit']"
    )

    submit_button.click()

    # Allow telemetry/session_transmitter.js to send.
    page.wait_for_timeout(2500)

    print("[Playwright Bot] Form submitted.")

    browser.close()


# ─────────────────────────────────────────────────────────────────────────────
# Step 4 — Verify experiment
# ─────────────────────────────────────────────────────────────────────────────

print("\n[Playwright Bot] Checking experiment status...")

time.sleep(1)

try:

    result = get(
        f"{API}/api/experiment/{experiment_id}"
    )

    if result.get("completed"):

        print("[Playwright Bot] ✅ Session saved")
        print(
            f"[Playwright Bot] Session ID: "
            f"{result.get('session_id')}"
        )

    else:

        print("[Playwright Bot] ⚠️ Experiment is still pending")
        print(
            "[Playwright Bot] The browser submitted, "
            "but /api/session may not have been received."
        )

except Exception as e:

    print("[Playwright Bot] Verification failed:")
    print(e)

