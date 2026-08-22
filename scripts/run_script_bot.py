"""Simulates a script bot — fills form instantly with no hesitation."""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get('http://localhost:8080/templates/login.html')
time.sleep(3)  # wait for page + probes to load

# Fill instantly with no human delay
driver.find_element(By.ID, 'email').send_keys('bot@test.com')
driver.find_element(By.ID, 'password').send_keys('password123')
time.sleep(1)
driver.find_element(By.CSS_SELECTOR, 'button[type=submit]').click()
time.sleep(2)
print('Script bot session submitted.')
input('Press Enter to close the browser...')
driver.quit()
