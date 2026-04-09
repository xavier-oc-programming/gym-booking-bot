import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import os
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from config import ADMIN_EMAIL, ADMIN_PASSWORD, DEFAULT_RETRIES, retry
from browser import GymBrowser
from booker import ClassBooker


def main() -> None:
    account_email = os.getenv("ACCOUNT_EMAIL")
    account_password = os.getenv("ACCOUNT_PASSWORD")

    if not account_email or not account_password:
        print("Error: ACCOUNT_EMAIL and ACCOUNT_PASSWORD must be set in .env or environment.")
        sys.exit(1)

    browser = GymBrowser()
    browser.open_gym()

    # ----------------------------------------------------------------
    # Phase 1 — Admin: enable network simulation for resilience testing
    # ----------------------------------------------------------------
    print("=== ADMIN PHASE ===")
    retry(
        lambda: browser.login(ADMIN_EMAIL, ADMIN_PASSWORD),
        description="Admin login",
    )

    # Enable network simulation via admin panel
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import NoSuchElementException, NoAlertPresentException

    driver = browser.driver
    try:
        checkbox = driver.find_element(
            By.XPATH, "//input[@type='checkbox' and contains(@id,'network')]"
        )
        if not checkbox.is_selected():
            checkbox.click()
            print("Network simulation enabled.")
    except NoSuchElementException:
        print("Network simulation checkbox not found — skipping.")

    try:
        slider = driver.find_element(
            By.XPATH, "//input[contains(@id,'failure') or contains(@name,'failure')]"
        )
        slider.clear()
        slider.send_keys("50")
        print("Failure rate set to 50%.")
    except NoSuchElementException:
        print("Failure rate input not found — skipping.")

    try:
        clear_btn = driver.find_element(By.XPATH, "//button[contains(., 'Clear Bookings Only')]")
        clear_btn.click()
        try:
            driver.switch_to.alert.accept()
            print("Cleared all bookings.")
        except NoAlertPresentException:
            pass
    except NoSuchElementException:
        print("Clear Bookings button not found — skipping.")

    try:
        driver.find_element(By.ID, "reset-time-button").click()
        print("Time reset to real time.")
    except NoSuchElementException:
        pass

    browser.logout()
    print("Admin setup complete. Network is now flaky.\n")

    # ----------------------------------------------------------------
    # Phase 2 — User: login and book classes
    # ----------------------------------------------------------------
    print("=== USER PHASE ===")
    retry(
        lambda: browser.login(account_email, account_password),
        description="User login",
        retries=DEFAULT_RETRIES,
    )

    booker = ClassBooker(browser)

    target_cards = booker.find_target_cards()
    print(f"Found {len(target_cards)} Tue/Thu 6:00 PM class(es) to process.")

    counts: list[int] = [0, 0, 0]  # [booked, waitlisted, already]

    for idx, card in enumerate(target_cards, start=1):
        def attempt(c=card):
            return booker.book_card(c)

        result = retry(attempt, description=f"Booking class {idx}", retries=DEFAULT_RETRIES)

        if result == "booked":
            counts[0] += 1
        elif result == "waitlisted":
            counts[1] += 1
        elif result and result.startswith("already"):
            counts[2] += 1

    print(f"\nNew bookings: {counts[0]}")
    print(f"Waitlists joined: {counts[1]}")
    print(f"Already booked/waitlisted: {counts[2]}")

    # ----------------------------------------------------------------
    # Phase 3 — Verify: open My Bookings page
    # ----------------------------------------------------------------
    print("\n=== VERIFICATION PHASE ===")
    def verify():
        booked, waitlisted = browser.open_my_bookings()
        total = booked + waitlisted
        print(f"My Bookings: {booked} booked, {waitlisted} waitlisted (total {total}).")
        return True

    retry(verify, description="My Bookings verification")

    print("\nResilient run complete. Inspect the browser to confirm results.")


if __name__ == "__main__":
    main()
