"""
browser.py — class GymBrowser

Handles all Chrome WebDriver setup, login, logout, and page navigation.
Pure driver logic — no booking decisions, no output files, no print summaries.
Raises exceptions on failure; does NOT call sys.exit().
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from config import GYM_URL, CHROME_PROFILE_DIR, WAIT_TIMEOUT, HEADLESS


class GymBrowser:
    """
    Manages the Chrome WebDriver session for the Snack & Lift gym site.
    Use as a context manager (with GymBrowser() as b:) or call quit() manually.
    """

    def __init__(self, headless: bool = HEADLESS):
        options = webdriver.ChromeOptions()
        CHROME_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        options.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR}")

        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")
        else:
            options.add_experimental_option("detach", True)

        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, WAIT_TIMEOUT)

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.quit()

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def open_gym(self) -> None:
        """Navigate to the gym homepage."""
        self.driver.get(GYM_URL)

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    def login(self, email: str, password: str) -> bool:
        """
        Attempt to log in with *email* and *password*.
        Returns True on success, False if a network-failure banner is detected.
        Raises TimeoutException if neither the schedule page nor a network error appears.
        """
        login_btn = self.wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
        login_btn.click()

        email_input = self.wait.until(EC.presence_of_element_located((By.ID, "email-input")))
        email_input.clear()
        email_input.send_keys(email)

        password_input = self.driver.find_element(By.ID, "password-input")
        password_input.clear()
        password_input.send_keys(password)

        self.driver.find_element(By.ID, "submit-button").click()

        try:
            self.wait.until(EC.presence_of_element_located((By.ID, "schedule-page")))
            return True
        except TimeoutException:
            banners = self.driver.find_elements(
                By.XPATH, "//*[contains(text(), 'Network request failed')]"
            )
            if banners:
                print("Network request failed during login. Will retry.")
                return False
            return True  # admin page likely loaded instead

    def logout(self) -> None:
        """Log out if the logout button is present; silently skip if not."""
        try:
            btn = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.ID, "logout-button"))
            )
            btn.click()
            time.sleep(0.5)
            print("Logged out.")
        except (TimeoutException, NoSuchElementException):
            print("No logout button found — already logged out or network failed.")

    # ------------------------------------------------------------------
    # Schedule page
    # ------------------------------------------------------------------
    def wait_for_schedule(self) -> None:
        """Block until the class schedule page is fully loaded."""
        self.wait.until(EC.presence_of_element_located((By.ID, "schedule-page")))

    def get_class_cards(self) -> list:
        """Return all class card WebElements currently visible on the schedule page."""
        self.wait_for_schedule()
        return self.driver.find_elements(By.CSS_SELECTOR, "div[id^='class-card-']")

    # ------------------------------------------------------------------
    # My Bookings page
    # ------------------------------------------------------------------
    def open_my_bookings(self) -> tuple[int, int]:
        """
        Navigate to My Bookings and return (booked_count, waitlisted_count).
        Re-clicks the tab once after a short delay to trigger a data refresh.
        """
        tab = self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "My Bookings")))
        tab.click()
        self.wait.until(EC.presence_of_element_located((By.ID, "my-bookings-page")))
        time.sleep(5)
        try:
            tab = self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "My Bookings")))
            tab.click()
        except TimeoutException:
            print("Warning: My Bookings tab not clickable for re-click refresh.")

        booked = self.driver.find_elements(By.CSS_SELECTOR, "div[id^='booking-card-']")
        waitlisted = self.driver.find_elements(By.CSS_SELECTOR, "div[id^='waitlist-card-']")
        return len(booked), len(waitlisted)

    # ------------------------------------------------------------------
    # Teardown
    # ------------------------------------------------------------------
    def quit(self) -> None:
        """Quit the WebDriver session (no-op if already quit)."""
        try:
            self.driver.quit()
        except Exception:
            pass
