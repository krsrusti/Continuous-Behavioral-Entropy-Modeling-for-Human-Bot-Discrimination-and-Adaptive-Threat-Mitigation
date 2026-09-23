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
    Deliberately consistent LLM-style inference delay.

    Slight variation is used so the timing is regular without being
    perfectly identical.
    """

    delay = 2.0

    print(
        f"[LLM] Thinking... {delay:.3f}s"
    )

    time.sleep(delay)


def robotic_mouse(driver):
    """
    Very regular mouse trajectory.

    Same target, same movement pattern, same pauses.
    """

    try:

        body = driver.find_element(
            By.TAG_NAME,
            "body"
        )

        actions = ActionChains(driver)

        actions.move_to_element(body)

        # Repeated, highly regular movement.

        for _ in range(8):

            actions.move_by_offset(
                40,
                20
            )

            actions.pause(
                0.10
            )

        actions.perform()

        print(
            "Performed robotic mouse pattern"
        )

        return True

    except Exception as e:

        print(
            f"Mouse movement failed: {e}"
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

        time.sleep(
            0.25
        )

    print(
        "Performed repeated scroll pattern"
    )


def robotic_click(driver):
    """
    Click Quick Actions buttons repeatedly.

    Uses the available Quick Action buttons and clicks several of them
    in a regular, deliberate pattern to generate more click telemetry.
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
            print("[LLM] No action buttons found")
            return False

        clicks = 0

        # Click several Quick Action buttons in sequence.
        for button in visible:
            if clicks >= 3:
                break

            try:
                # Consistent LLM-style hesitation before each click.
                time.sleep(1.0)

                button.click()
                clicks += 1

                print(
                    f"[LLM] Clicked Quick Action "
                    f"{clicks}/{min(3, len(visible))}"
                )

                # Short, regular pause after each click.
                time.sleep(0.5)

            except Exception as e:
                print(f"[LLM] Quick Action click failed: {e}")

        return clicks > 0

    except Exception as e:
        print(f"[LLM] Click failed: {e}")
        return False


def check_termination(driver):

    try:

        overlay = driver.find_element(
            By.ID,
            "terminate-overlay"
        )

        classes = overlay.get_attribute(
            "class"
        )

        return "active" in classes

    except Exception:

        return False


def main():

    print()
    print("=" * 60)
    print("DETECTION TEST")
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

        print(
            "Start Chrome with:"
        )

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
        "[TEST] Starting deliberately..."
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

        # -----------------------------------------------------------
        # 1. Consistent reasoning delay
        # -----------------------------------------------------------

        fixed_think()

        # -----------------------------------------------------------
        # 2. Repeated mouse trajectory
        # -----------------------------------------------------------

        if robotic_mouse(driver):

            actions_taken += 1

        # -----------------------------------------------------------
        # 3. Repeated scroll pattern
        # -----------------------------------------------------------

        robotic_scroll(driver)

        actions_taken += 1

        # -----------------------------------------------------------
        # 4. Repeated action-button interaction
        # -----------------------------------------------------------

        if robotic_click(driver):

            actions_taken += 1

        # -----------------------------------------------------------
        # 5. Small fixed pause
        # -----------------------------------------------------------

        time.sleep(
            1.0
        )

        # -----------------------------------------------------------
        # 6. Check termination
        # -----------------------------------------------------------

        if check_termination(driver):

            print()

            print("=" * 60)
            print(" DETECTED")
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
        "[TEST]interaction sequence finished."
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
            print("DETECTED")
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
        "  prediction = bot"
    )

    print(
        "  action     = terminate"
    )


if __name__ == "__main__":
    main()