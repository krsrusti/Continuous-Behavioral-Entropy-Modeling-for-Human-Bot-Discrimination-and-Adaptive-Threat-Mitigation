"""
llm_artificial_test.py

Artificial / highly regular LLM-style takeover test.

Purpose:
    Stress-test the account.html detection pipeline with behavior that
    should be substantially different from normal human interaction.

Usage:
    1. Start Chrome:
       chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\\chrome-debug"

    2. Log in normally and open account.html.

    3. Wait a few seconds.

    4. Run:
       python scripts/llm/llm_artificial_test.py
"""

import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains


def attach_to_chrome():
    options = Options()
    options.add_experimental_option(
        "debuggerAddress",
        "localhost:9222"
    )

    return webdriver.Chrome(options=options)


def fixed_think():
    """
    Deliberately identical inference delay every time.
    """
    print("[LLM] Thinking... 2.000s")
    time.sleep(2.0)


def robotic_mouse(driver):
    """
    Very regular mouse trajectory.

    Same target, same movement pattern, same pauses.
    """

    try:
        body = driver.find_element(By.TAG_NAME, "body")

        actions = ActionChains(driver)

        actions.move_to_element(body)

        for _ in range(8):
            actions.move_by_offset(40, 20)
            actions.pause(0.10)

        actions.perform()

        print("[LLM] Performed robotic mouse pattern")

        return True

    except Exception as e:
        print(
            f"[LLM] Mouse movement failed: {e}"
        )

        return False


def robotic_scroll(driver):
    """
    Repeated identical scroll operations.
    """

    for _ in range(3):
        driver.execute_script(
            "window.scrollBy(0, 200)"
        )

        time.sleep(0.25)

    print(
        "[LLM] Performed repeated scroll pattern"
    )


def robotic_click(driver):
    """
    Repeatedly select the first available action button.
    """

    try:
        buttons = driver.find_elements(
            By.CLASS_NAME,
            "action-btn"
        )

        visible = [
            button
            for button in buttons
            if button.is_displayed() and button.is_enabled()
        ]

        if not visible:
            print(
                "[LLM] No action button found"
            )

            return False

        visible[0].click()

        print(
            "[LLM] Clicked first action button"
        )

        return True

    except Exception as e:

        print(
            f"[LLM] Click failed: {e}"
        )

        return False


def check_termination(driver):

    try:

        overlay = driver.find_element(
            By.ID,
            "terminate-overlay"
        )

        classes = overlay.get_attribute("class")

        return "active" in classes

    except Exception:

        return False


def main():

    print()
    print("=" * 60)
    print("LLM DETECTION TEST")
    print("=" * 60)
    print()

    print(
        "[TEST] Connecting to existing Chrome..."
    )

    try:

        driver = attach_to_chrome()

    except Exception as e:

        print(
            f"[ERROR] Could not connect to Chrome: {e}"
        )

        print()
        print("Start Chrome with:")
        print(
            'chrome.exe --remote-debugging-port=9222 '
            '--user-data-dir="C:\\chrome-debug"'
        )

        return

    print(
        f"[TEST] Current URL: {driver.current_url}"
    )

    if "account" not in driver.current_url.lower():

        print()
        print(
            "[ERROR] You are not on account.html."
        )

        print(
            "Open the account page first."
        )

        return

    print()
    print(
        "[TEST] Account page detected."
    )

    print(
        "[TEST] Starting deliberately artificial behavior..."
    )

    time.sleep(2)

    actions_taken = 0

    # ---------------------------------------------------------------
    # Repeated highly regular behavior
    # ---------------------------------------------------------------

    for i in range(1, 16):

        print()
        print(
            f"==========  ACTION {i}/15 =========="
        )

        # Exactly the same reasoning delay.
        fixed_think()

        # Exactly the same mouse pattern.
        if robotic_mouse(driver):
            actions_taken += 1

        # Exactly the same scroll pattern.
        robotic_scroll(driver)

        actions_taken += 1

        # Exactly the same click target.
        if robotic_click(driver):
            actions_taken += 1

        # Fixed pause between action bursts.
        time.sleep(1.0)

        # Check whether account.html detected us.
        if check_termination(driver):

            print()
            print("=" * 60)
            print("LLM DETECTED")
            print("=" * 60)
            print()
            print(
                "account.html activated the termination overlay."
            )

            print(
                f"Actions performed: {actions_taken}"
            )

            return

    # ---------------------------------------------------------------
    # Final monitoring period
    # ---------------------------------------------------------------

    print()
    print(
        "[TEST] interaction sequence finished."
    )

    print(
        "[TEST] Waiting for account.html monitoring..."
    )

    for second in range(1, 16):

        time.sleep(1)

        print(
            f"[TEST] Monitoring... {second}/15"
        )

        if check_termination(driver):

            print()
            print("=" * 60)
            print("LLM DETECTED")
            print("=" * 60)
            return

    print()
    print("=" * 60)
    print(" TEST NOT DETECTED")
    print("=" * 60)
    print()

    print(
        "If this happens, inspect the /api/risk responses "
        "in the browser console."
    )

    print()
    print(
        "You should look for:"
    )

    print(
        "  prediction = llm"
    )

    print(
        "  action     = terminate"
    )


if __name__ == "__main__":
    main()