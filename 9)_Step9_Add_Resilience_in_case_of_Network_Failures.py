"""
9)_Step9_Add_Resilience_in_case_of_Network_Failures.py

Final Step:
-----------
This version makes your gym booking bot resilient against simulated network failures.

Features:
- Detects "Network request failed" errors and retries automatically.
- Handles missing logout buttons safely (when already logged out).
- Waits for bookings data to load on "My Bookings" page.
- Recovers from flaky or delayed page loads gracefully.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
    UnexpectedAlertPresentException,
    NoAlertPresentException,
)
import os
import time

# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------
GYM_URL = "https://appbrewery.github.io/gym/"

ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "admin123"

ACCOUNT_EMAIL = "xavierleisure@gmail.com"
ACCOUNT_PASSWORD = "getfit123"

DEFAULT_RETRIES = 7

# ---------------------------------------------------------------------
# DRIVER SETUP
# ---------------------------------------------------------------------
chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("detach", True)

# Persistent browser profile for cookies, sessions, and saved state
user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
os.makedirs(user_data_dir, exist_ok=True)
chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 5)
driver.get(GYM_URL)

# ---------------------------------------------------------------------
# RETRY WRAPPER
# ---------------------------------------------------------------------
def retry(func, retries=DEFAULT_RETRIES, description=None):
    """
    Retry a function up to `retries` times.
    If it raises, try again. If it returns falsy, try again.
    Return on first success.
    """
    last_exception = None
    for attempt in range(1, retries + 1):
        try:
            result = func()
            if result:
                if description:
                    print(f"{description} succeeded on attempt {attempt}.")
                return result
            else:
                print(f"{description or 'Operation'} returned falsy on attempt {attempt}, retrying...")
        except (NoSuchElementException, TimeoutException, WebDriverException, UnexpectedAlertPresentException) as e:
            last_exception = e
            print(f"{description or 'Operation'} failed on attempt {attempt}: {e.__class__.__name__}. Retrying...")
            time.sleep(0.5)
    print(f"{description or 'Operation'} failed after {retries} attempts.")
    if last_exception:
        raise last_exception
    return None

# ---------------------------------------------------------------------
# BASIC ACTIONS
# ---------------------------------------------------------------------
def login(email: str, password: str):
    """Try to log in. Returns True if successful, False if network failed."""
    login_btn = wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
    login_btn.click()

    email_input = wait.until(EC.presence_of_element_located((By.ID, "email-input")))
    email_input.clear()
    email_input.send_keys(email)

    password_input = driver.find_element(By.ID, "password-input")
    password_input.clear()
    password_input.send_keys(password)

    submit_btn = driver.find_element(By.ID, "submit-button")
    submit_btn.click()

    # Wait for schedule or admin page — or detect network failure
    try:
        wait.until(EC.presence_of_element_located((By.ID, "schedule-page")))
        return True
    except TimeoutException:
        # Check if the login failed due to network error
        error_banners = driver.find_elements(
            By.XPATH, "//*[contains(text(), 'Network request failed')]"
        )
        if error_banners:
            print("Network request failed during login. Retrying...")
            return False
        # Otherwise assume admin page loaded (fine)
        return True


def logout():
    """Log out safely if logout button is visible."""
    try:
        logout_btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.ID, "logout-button"))
        )
        logout_btn.click()
        time.sleep(0.5)
        print("Logged out successfully.")
    except (TimeoutException, NoSuchElementException):
        print("No logout button found — likely already logged out or network failed.")

# ---------------------------------------------------------------------
# ADMIN PANEL ACTIONS
# ---------------------------------------------------------------------
def admin_enable_network_simulation():
    """
    In the Admin Panel:
    - Enable Network Simulation
    - Set failure rate to 50%
    - Click "Clear Bookings Only" (and accept alert)
    - Reset time to Real Time
    """
    try:
        net_checkbox = driver.find_element(
            By.XPATH, "//input[@type='checkbox' and contains(@id,'network')]"
        )
        if not net_checkbox.is_selected():
            net_checkbox.click()
            print("Network simulation enabled.")
        else:
            print("Network simulation already enabled.")
    except NoSuchElementException:
        print("Could not find network simulation checkbox.")

    # Set failure rate (best effort)
    try:
        failure_slider = driver.find_element(
            By.XPATH, "//input[contains(@id,'failure') or contains(@name,'failure')]"
        )
        failure_slider.clear()
        failure_slider.send_keys("50")
        print("Failure rate set to 50%.")
    except NoSuchElementException:
        print("Failure rate input not found. Leaving default value.")

    # Clear bookings (with alert handling)
    try:
        clear_btn = driver.find_element(
            By.XPATH, "//button[contains(., 'Clear Bookings Only')]"
        )
        clear_btn.click()
        try:
            alert = driver.switch_to.alert
            alert.accept()
            print("Cleared all bookings (alert accepted).")
        except NoAlertPresentException:
            print("No alert appeared after clearing bookings.")
    except NoSuchElementException:
        print("Could not find 'Clear Bookings Only' button.")

    # Reset time to real time
    try:
        reset_time_btn = driver.find_element(By.ID, "reset-time-button")
        reset_time_btn.click()
        print("Time reset to real time.")
    except NoSuchElementException:
        print("Reset time button not found. Skipping.")

    return True

# ---------------------------------------------------------------------
# USER BOOKING ACTIONS
# ---------------------------------------------------------------------
def find_tue_thu_6pm_class_cards():
    """Find all Tuesday/Thursday 6:00 PM class cards."""
    wait.until(EC.presence_of_element_located((By.ID, "schedule-page")))
    cards = driver.find_elements(By.CSS_SELECTOR, "div[id^='class-card-']")
    targets = []

    for card in cards:
        day_group = card.find_element(
            By.XPATH, "./ancestor::div[contains(@id, 'day-group-')]"
        )
        day_title = day_group.find_element(By.TAG_NAME, "h2").text

        if "Tue" in day_title or "Thu" in day_title:
            time_text = card.find_element(
                By.CSS_SELECTOR, "p[id^='class-time-']"
            ).text
            if "6:00 PM" in time_text:
                targets.append(card)

    return targets


def book_class_card(card):
    """Try to book or join waitlist for one card."""
    button = card.find_element(By.CSS_SELECTOR, "button[id^='book-button-']")
    label = button.text.strip().lower()

    if "book class" in label or "join waitlist" in label:
        button.click()
        return True
    if "booked" in label or "waitlisted" in label:
        return True
    return False



def get_my_bookings_page():
    """Open 'My Bookings', wait for UI to stabilize, refresh it, then read the actual bookings."""
    # 1) Click the tab the first time
    my_bookings_tab = wait.until(
        EC.element_to_be_clickable((By.LINK_TEXT, "My Bookings"))
    )
    my_bookings_tab.click()

    # 2) Wait for the page container to exist
    wait.until(EC.presence_of_element_located((By.ID, "my-bookings-page")))

    # 3) Give the page time to mount React components before forcing refresh
    time.sleep(5)

    # 4) Re-click the tab to trigger data fetch / state update
    try:
        my_bookings_tab = wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "My Bookings"))
        )
        my_bookings_tab.click()
    except TimeoutException:
        # If the button isn't found quickly, proceed without interrupting the flow
        print("Warning: My Bookings tab not clickable for re-click refresh.")
        pass

    # 5) After the refresh, gather booking and waitlist data
    booking_cards = driver.find_elements(By.CSS_SELECTOR, "div[id^='booking-card-']")
    waitlist_cards = driver.find_elements(By.CSS_SELECTOR, "div[id^='waitlist-card-']")
    total = len(booking_cards) + len(waitlist_cards)

    print(
        f"My Bookings loaded — {len(booking_cards)} booked, "
        f"{len(waitlist_cards)} waitlisted (total {total})."
    )
    return True



# ---------------------------------------------------------------------
# MAIN SCRIPT FLOW
# ---------------------------------------------------------------------

# 1) ADMIN PHASE – PREPARE THE CHAOS
retry(lambda: login(ADMIN_EMAIL, ADMIN_PASSWORD), description="Admin login")
admin_enable_network_simulation()
logout()
print("\nAdmin setup complete. Network is now flaky.\n")

# 2) USER PHASE – LOGIN (WITH RETRIES)
retry(lambda: login(ACCOUNT_EMAIL, ACCOUNT_PASSWORD), description="User login")

# 3) BOOK CLASSES (TUE/THU 6PM)
target_cards = find_tue_thu_6pm_class_cards()
print(f"Found {len(target_cards)} Tue/Thu 6:00 PM class(es) to process.")

processed = 0
for idx, card in enumerate(target_cards, start=1):
    def work():
        return book_class_card(card)
    retry(work, description=f"Booking class {idx}")
    processed += 1

print(f"\nFinished attempting to book/waitlist {processed} class(es).")

# 4) VERIFY BOOKINGS PAGE
retry(get_my_bookings_page, description="My Bookings verification")

print("\nResilient run complete. Inspect the browser to confirm results.")
