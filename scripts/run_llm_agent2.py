
"""run_llm_agent_evasion.py — LLM agent that mimics human mouse movements."""

import requests
import time
import random

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
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
        "notes": "LLM evasion variant with simulated mouse movements"
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
print("LLM EVASION EXPERIMENT CREATED")
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

# Wait for page + telemetry + probes
time.sleep(3)


# ─────────────────────────────────────────────────────────────
# 4. Simulate LLM thinking
# ─────────────────────────────────────────────────────────────

def llm_think():
    """Simulates LLM inference delay."""
    time.sleep(random.uniform(0.8, 2.0))


# ─────────────────────────────────────────────────────────────
# 5. Simulated mouse movement
# ─────────────────────────────────────────────────────────────

def fake_human_mouse():
    """
    Generates small mouse movements inside the browser window.
    """

    size = driver.get_window_size()

    width = size["width"]
    height = size["height"]

    actions = ActionChains(driver)

    # Start from centre of the page
    body = driver.find_element(By.TAG_NAME, "body")

    actions.move_to_element(body)

    # Small relative movements
    for _ in range(random.randint(5, 10)):

        dx = random.randint(-50, 50)
        dy = random.randint(-30, 30)

        actions.move_by_offset(dx, dy)

        actions.pause(
            random.uniform(0.05, 0.2)
        )

    actions.perform()


# ─────────────────────────────────────────────────────────────
# 6. LLM interaction sequence
# ─────────────────────────────────────────────────────────────

fake_human_mouse()

llm_think()


email_field = driver.find_element(
    By.ID,
    "email"
)

email_field.click()

llm_think()

email_field.send_keys(
    "llm@evasion.com"
)

llm_think()


# Additional mouse activity
fake_human_mouse()

llm_think()


password_field = driver.find_element(
    By.ID,
    "password"
)

password_field.click()

llm_think()

password_field.send_keys(
    "password123"
)

llm_think()


# Additional mouse activity
fake_human_mouse()

llm_think()


# ─────────────────────────────────────────────────────────────
# 7. Submit form
# ─────────────────────────────────────────────────────────────

driver.find_element(
    By.CSS_SELECTOR,
    "button[type=submit]"
).click()


# Give /api/session time to complete
time.sleep(3)


print("\n========================================")
print("LLM EVASION SESSION SUBMITTED")
print("========================================")
print("Experiment ID :", experiment_id)
print("Participant ID:", participant_id)


# ─────────────────────────────────────────────────────────────
# 8. Close browser
# ─────────────────────────────────────────────────────────────

driver.quit()

