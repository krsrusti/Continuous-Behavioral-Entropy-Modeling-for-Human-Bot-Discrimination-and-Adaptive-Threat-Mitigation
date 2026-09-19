"""
llm_mid_session_attack.py

Attaches to an existing Chrome session and simulates an LLM agent
taking over mid-session while a human is on the account page.

Usage:
    1. Launch Chrome with remote debugging:
       chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\\chrome-debug"

    2. Open login page, fill form, land on account page
    3. Interact normally for 15-20 seconds
    4. Run this script:
       python scripts/llm/llm_mid_session_attack.py

    Watch the account page freeze with TERMINATED message.
"""
import time
import random
import json
import urllib.request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains


API = 'http://localhost:5000'


def get(url):
    return json.loads(urllib.request.urlopen(url, timeout=10).read())


def llm_think(min_ms=800, max_ms=2000):
    """
    Simulates LLM inference delay.
    This is the gap the probe captures.
    """
    delay = random.uniform(min_ms / 1000, max_ms / 1000)
    print(f'  [LLM] Thinking... ({delay*1000:.0f}ms)')
    time.sleep(delay)


def attach_to_existing_chrome():
    """Attach Selenium to the already-open Chrome window."""
    options = Options()
    options.add_experimental_option('debuggerAddress', 'localhost:9222')
    driver = webdriver.Chrome(options=options)
    return driver


def run_mid_session_attack():
    print('\n[LLM Attack] Attaching to existing Chrome session...')

    try:
        driver = attach_to_existing_chrome()
    except Exception as e:
        print(f'[ERROR] Cannot attach to Chrome: {e}')
        print('Make sure Chrome is running with:')
        print('  chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\\\\chrome-debug"')
        return

    print(f'[LLM Attack] Attached to: {driver.current_url}')

    # Verify we are on the account page
    if 'account' not in driver.current_url:
        print('[ERROR] Not on the account page.')
        print('Please navigate to the account page first, then run this script.')
        return

    print('[LLM Attack] ✅ On account page — starting mid-session attack in 3 seconds...')
    print('[LLM Attack] Watch the page for the TERMINATED overlay!\n')
    time.sleep(3)

    # ── Phase 1: LLM observes the page ────────────────────────────────────────
    print('[LLM Attack] Phase 1: Observing page...')
    llm_think(1000, 2500)

    # ── Phase 2: LLM starts interacting ───────────────────────────────────────
    print('[LLM Attack] Phase 2: Starting interaction...')

    actions_taken = 0

    # Action 1 — scroll down slowly (LLM observing)
    llm_think()
    try:
        driver.execute_script('window.scrollBy(0, 200)')
        print('[LLM Attack] Action 1: Scrolled down')
        actions_taken += 1
    except Exception as e:
        print(f'[LLM Attack] Scroll failed: {e}')

    # Action 2 — click a quick action button
    llm_think()
    try:
        buttons = driver.find_elements(By.CLASS_NAME, 'action-btn')
        if buttons:
            buttons[0].click()
            print('[LLM Attack] Action 2: Clicked action button')
            actions_taken += 1
    except Exception as e:
        print(f'[LLM Attack] Button click failed: {e}')

    # Action 3 — move mouse to balance card (LLM examining)
    llm_think(1200, 2200)
    try:
        actions = ActionChains(driver)
        balance = driver.find_element(By.CLASS_NAME, 'balance-card')
        actions.move_to_element(balance).perform()
        print('[LLM Attack] Action 3: Moved to balance card')
        actions_taken += 1
    except Exception as e:
        print(f'[LLM Attack] Mouse move failed: {e}')

    # Action 4 — click transfer button
    llm_think()
    try:
        bal_btns = driver.find_elements(By.CLASS_NAME, 'bal-btn')
        if bal_btns:
            bal_btns[0].click()
            print('[LLM Attack] Action 4: Clicked Transfer button')
            actions_taken += 1
    except Exception as e:
        print(f'[LLM Attack] Transfer click failed: {e}')

    # Action 5 — scroll back up
    llm_think(900, 1800)
    try:
        driver.execute_script('window.scrollTo(0, 0)')
        print('[LLM Attack] Action 5: Scrolled back to top')
        actions_taken += 1
    except Exception as e:
        print(f'[LLM Attack] Scroll failed: {e}')

    # Action 6 — click another action button
    llm_think()
    try:
        buttons = driver.find_elements(By.CLASS_NAME, 'action-btn')
        if len(buttons) > 1:
            buttons[1].click()
            print('[LLM Attack] Action 6: Clicked second action button')
            actions_taken += 1
    except Exception as e:
        print(f'[LLM Attack] Button click failed: {e}')

    # ── Phase 3: Wait for system to detect ────────────────────────────────────
    print(f'\n[LLM Attack] {actions_taken} actions taken with LLM think delays')
    print('[LLM Attack] Waiting for continuous monitoring to detect...')
    time.sleep(5)

    # ── Phase 4: Check if terminated ──────────────────────────────────────────
    try:
        overlay = driver.find_element(By.ID, 'terminate-overlay')
        overlay_visible = overlay.get_attribute('class')
        if 'active' in overlay_visible:
            print('\n[LLM Attack] 🚫 SESSION TERMINATED — System detected the LLM agent!')
            print('[LLM Attack] The probe captured inference latency during think delays.')
        else:
            print('\n[LLM Attack] ⚠️  Overlay not yet visible.')
            print('[LLM Attack] Risk may need more actions to trigger.')
            print('[LLM Attack] Check alerts page: http://localhost:8080/templates/alerts.html')
    except Exception as e:
        print(f'[LLM Attack] Could not check overlay: {e}')

    # ── Phase 5: Show session stats ───────────────────────────────────────────
    print('\n[LLM Attack] Checking session stats...')
    time.sleep(2)
    try:
        stats = get(f'{API}/api/sessions/stats')
        print(f'[LLM Attack] Total sessions: {stats["total"]}')
        for cls, d in stats['by_class'].items():
            if d['total'] > 0:
                print(f'  {cls}: {d["total"]} sessions')
    except Exception as e:
        print(f'[LLM Attack] Could not get stats: {e}')

    print('\n[LLM Attack] Attack complete.')
    print('[LLM Attack] Check the account page for the TERMINATED overlay.')


if __name__ == '__main__':
    run_mid_session_attack()