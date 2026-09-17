"""Simulates a script bot and automatically creates its own experiment."""

import requests
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


API = "http://localhost:5000"
LOGIN_PAGE = "http://localhost:8080/templates/login.html"


# ─────────────────────────────────────────────────────────────
# 1. Create a new BOT experiment
# ─────────────────────────────────────────────────────────────

response = requests.post(
    f"{API}/api/experiment/start",
    json={
        "agent_class": "bot",
        "task_id": "login",
        "probe_enabled": True,
        "notes": "Automatically generated script bot session"
    }
)

if response.status_code != 201:
    print("Failed to create experiment.")
    print(response.status_code)
    print(response.text)
    raise SystemExit(1)


experiment = response.json()

experiment_id = experiment["experiment_id"]
participant_id = experiment["participant_id"]
task_id = experiment["task_id"]
probe_enabled = experiment["probe_enabled"]


print("\n========================================")
print("BOT EXPERIMENT CREATED")
print("========================================")
print("Experiment ID :", experiment_id)
print("Participant ID:", participant_id)
print("Task ID       :", task_id)
print("Probe enabled :", probe_enabled)


# ─────────────────────────────────────────────────────────────
# 2. Build experiment-specific URL automatically
# ─────────────────────────────────────────────────────────────

login_url = (
    f"{LOGIN_PAGE}"
    f"?experiment_id={experiment_id}"
    f"&participant_id={participant_id}"
    f"&probe_enabled={'true' if probe_enabled else 'false'}"
    f"&task_id={task_id}"
)

print("\nOpening:")
print(login_url)


# ─────────────────────────────────────────────────────────────
# 3. Start Selenium
# ─────────────────────────────────────────────────────────────

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install())
)

driver.get(login_url)

# Allow page, telemetry and probes to load
time.sleep(3)


# ─────────────────────────────────────────────────────────────
# 4. Perform bot behaviour
# ─────────────────────────────────────────────────────────────

driver.find_element(
    By.ID,
    "email"
).send_keys("bot@test.com")

driver.find_element(
    By.ID,
    "password"
).send_keys("password123")

# Small bot delay
time.sleep(1)


# ─────────────────────────────────────────────────────────────
# 5. Submit form
# ─────────────────────────────────────────────────────────────

driver.find_element(
    By.CSS_SELECTOR,
    "button[type=submit]"
).click()


# Give the browser time to send /api/session
time.sleep(3)


print("\n========================================")
print("BOT SESSION SUBMITTED")
print("========================================")
print("Experiment ID :", experiment_id)
print("Participant ID:", participant_id)


# ─────────────────────────────────────────────────────────────
# 6. Close browser
# ─────────────────────────────────────────────────────────────

driver.quit()