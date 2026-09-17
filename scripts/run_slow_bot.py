"""
run_slow_bot.py
Simulates a slower deterministic Selenium bot.

Unlike the instant bot, this bot:
- waits a fixed amount of time between actions
- moves directly to elements
- performs normal Selenium interactions
- uses the experiment-specific URL automatically
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import urllib.request
import json
import time


# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

API = "http://localhost:5000"
PAGE_BASE = "http://localhost:8080/templates/login.html"


# ─────────────────────────────────────────────────────────────────────────────
# HELPER — POST JSON
# ─────────────────────────────────────────────────────────────────────────────

def post(url, data):
    payload = json.dumps(data).encode()

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read())


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — CREATE EXPERIMENT
# ─────────────────────────────────────────────────────────────────────────────

print("[Slow Bot] Registering experiment...")

exp = post(
    f"{API}/api/experiment/start",
    {
        "agent_class": "bot",
        "task_id": "login",
        "probe_enabled": True,
        "notes": "slow deterministic selenium bot"
    }
)

print("[Slow Bot] Experiment ID :", exp["experiment_id"])
print("[Slow Bot] Participant ID:", exp["participant_id"])


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — BUILD EXPERIMENT-SPECIFIC URL
# ─────────────────────────────────────────────────────────────────────────────

session_url = (
    f"{PAGE_BASE}"
    f"?experiment_id={exp['experiment_id']}"
    f"&participant_id={exp['participant_id']}"
    f"&probe_enabled=true"
    f"&task_id=login"
)

print("[Slow Bot] Session URL:", session_url)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — START BROWSER
# ─────────────────────────────────────────────────────────────────────────────

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install())
)

driver.get(session_url)

# Give page and telemetry time to initialize
time.sleep(3)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — BOT ACTIONS
# ─────────────────────────────────────────────────────────────────────────────

print("[Slow Bot] Starting actions...")


# Move directly to email field
email = driver.find_element(By.ID, "email")

ActionChains(driver).move_to_element(email).perform()

time.sleep(1)

email.click()

time.sleep(0.5)

email.send_keys("slowbot@test.com")

time.sleep(2)


# Move directly to password field
password = driver.find_element(By.ID, "password")

ActionChains(driver).move_to_element(password).perform()

time.sleep(1)

password.click()

time.sleep(0.5)

password.send_keys("password123")

time.sleep(2)


# Move directly to submit button
button = driver.find_element(
    By.CSS_SELECTOR,
    "button[type=submit]"
)

ActionChains(driver).move_to_element(button).perform()

time.sleep(1)

button.click()

print("[Slow Bot] Form submitted.")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — WAIT FOR SESSION TRANSMISSION
# ─────────────────────────────────────────────────────────────────────────────

time.sleep(3)

print("[Slow Bot] Finished.")

driver.quit()