"""Simulates an LLM agent — pauses to 'think' between each action."""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time, random

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get('http://localhost:8080/templates/login.html')
time.sleep(3)  # wait for page + probes to load

def llm_think():
    """Simulates LLM inference delay — 800ms to 2000ms."""
    time.sleep(random.uniform(0.8, 2.0))

# LLM agents pause before every single action
llm_think()
driver.find_element(By.ID, 'email').click()
llm_think()
driver.find_element(By.ID, 'email').send_keys('llmagent@test.com')
llm_think()
driver.find_element(By.ID, 'password').click()
llm_think()
driver.find_element(By.ID, 'password').send_keys('password123')
llm_think()
driver.find_element(By.CSS_SELECTOR, 'button[type=submit]').click()
time.sleep(2)
print('LLM agent session submitted.')
input("Press Enter to close the browser...")
driver.quit()