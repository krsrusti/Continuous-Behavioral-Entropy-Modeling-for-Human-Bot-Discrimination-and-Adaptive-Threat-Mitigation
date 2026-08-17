"""run_llm_agent_evasion.py — LLM agent that mimics human mouse movements."""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import time, random

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get('http://localhost:8080/templates/login.html')
time.sleep(3)

def llm_think():
    time.sleep(random.uniform(0.8, 2.0))

def fake_human_mouse():
    """Moves mouse in small increments — stays within window bounds."""
    # Get window size to stay within bounds
    size    = driver.get_window_size()
    width   = size['width']
    height  = size['height']

    actions = ActionChains(driver)
    # Start from centre of page
    actions.move_to_element(driver.find_element(By.TAG_NAME, 'body'))

    # Small relative movements — never go out of bounds
    for _ in range(random.randint(5, 10)):
        dx = random.randint(-50, 50)
        dy = random.randint(-30, 30)
        actions.move_by_offset(dx, dy)
        actions.pause(random.uniform(0.05, 0.2))

    actions.perform()

# Fake mouse to fool BEI detectors
fake_human_mouse()
llm_think()

email_field = driver.find_element(By.ID, 'email')
email_field.click()
llm_think()
email_field.send_keys('llm@evasion.com')
llm_think()

fake_human_mouse()
llm_think()

password_field = driver.find_element(By.ID, 'password')
password_field.click()
llm_think()
password_field.send_keys('password123')
llm_think()

fake_human_mouse()
llm_think()

driver.find_element(By.CSS_SELECTOR, 'button[type=submit]').click()
time.sleep(2)
print('Evasion agent session submitted.')

input("Press Enter to close the browser...")
driver.quit()
