"""Simulates an LLM agent and automatically creates its own experiment."""

import requests
import time
import random

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


API = "http://localhost:5000"
LOGIN_PAGE = "http://localhost:8080/templates/login.html"


# ─────────────────────────────────────────────────────────────
# 1. Create a new LLM experiment automatically
# ─────────────────────────────────────────────────────────────

response = requests.post(
    f"{API}/api/experiment/start",
    json={
        "agent_class": "llm",
        "task_id": "login",
        "probe_enabled": True,
        "notes": "Automatically generated LLM session"
    }
)

if response.status_code != 201:
    print("Failed to create LLM experiment.")
    print("Status:", response.status_code)
    print("Response:", response.text)
    raise SystemExit(1)


experiment = response.json()

experiment_id = experiment["experiment_id"]
participant_id = experiment["participant_id"]
task_id = experiment["task_id"]
probe_enabled = experiment["probe_enabled"]


print("\n========================================")
print("LLM EXPERIMENT CREATED")
print("========================================")
print("Experiment ID :", experiment_id)
print("Participant ID:", participant_id)
print("Task ID       :", task_id)
print("Probe enabled :", probe_enabled)


# ─────────────────────────────────────────────────────────────
# 2. Build experiment-specific URL
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

# Wait for page + telemetry + probes
time.sleep(3)


# ─────────────────────────────────────────────────────────────
# 4. Simulate LLM thinking
# ─────────────────────────────────────────────────────────────

def llm_think():
    """
    Simulates an LLM inference delay.
    The delay is intentionally different for each action.
    """
    delay = random.uniform(0.8, 2.0)
    time.sleep(delay)


# ─────────────────────────────────────────────────────────────
# 5. LLM interaction sequence
# ─────────────────────────────────────────────────────────────

llm_think()

driver.find_element(
    By.ID,
    "email"
).click()


llm_think()

driver.find_element(
    By.ID,
    "email"
).send_keys("llmagent@test.com")


llm_think()

driver.find_element(
    By.ID,
    "password"
).click()


llm_think()

driver.find_element(
    By.ID,
    "password"
).send_keys("password123")


llm_think()


# ─────────────────────────────────────────────────────────────
# 6. Submit
# ─────────────────────────────────────────────────────────────

driver.find_element(
    By.CSS_SELECTOR,
    "button[type=submit]"
).click()


# Give /api/session time to complete
time.sleep(3)


print("\n========================================")
print("LLM SESSION SUBMITTED")
print("========================================")
print("Experiment ID :", experiment_id)
print("Participant ID:", participant_id)


# ─────────────────────────────────────────────────────────────
# 7. Close browser
# ─────────────────────────────────────────────────────────────

driver.quit()