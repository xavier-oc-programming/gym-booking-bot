"""
booker.py — class ClassBooker

Finds target class cards and books / joins the waitlist for each one.
Pure logic — no driver setup, no print summaries, no file I/O.
Raises exceptions on failure; does NOT call sys.exit().
"""

import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from selenium.webdriver.common.by import By

from config import TARGET_DAYS, TARGET_TIME
from browser import GymBrowser


class ClassBooker:
    """
    Operates on the class schedule page to find and book target sessions.

    Parameters
    ----------
    browser : GymBrowser
        An authenticated GymBrowser instance with the schedule page loaded.
    """

    def __init__(self, browser: GymBrowser):
        self._browser = browser

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------
    def find_target_cards(
        self,
        target_days: tuple = TARGET_DAYS,
        target_time: str = TARGET_TIME,
    ) -> list:
        """
        Return all class card WebElements that match *target_days* and *target_time*.
        Reads the current schedule page — call after login and schedule load.
        """
        import datetime
        self._browser.wait_for_schedule()
        driver = self._browser.driver
        today_is_target = datetime.date.today().weekday() in (1, 3)  # 1=Tue, 3=Thu

        cards = self._browser.get_class_cards()
        results = []

        for card in cards:
            day_group = card.find_element(
                By.XPATH, "./ancestor::div[contains(@id, 'day-group-')]"
            )
            day_title = day_group.find_element(By.TAG_NAME, "h2").text

            if not any(day in day_title for day in target_days):
                if not (today_is_target and "Today" in day_title):
                    continue

            time_text = card.find_element(By.CSS_SELECTOR, "p[id^='class-time-']").text
            if target_time in time_text:
                results.append(card)

        return results

    def book_card(self, card) -> str:
        """
        Attempt to book or join the waitlist for *card*.

        Returns
        -------
        str
            One of: "booked", "waitlisted", "already_booked",
            "already_waitlisted", or "" (falsy) if network failed.
        """
        button = card.find_element(By.CSS_SELECTOR, "button[id^='book-button-']")
        label = button.text.strip().lower()

        if "booked" in label:
            return "already_booked"
        if "waitlisted" in label:
            return "already_waitlisted"
        if "book class" in label or "join waitlist" in label:
            button.click()
            for _ in range(6):  # wait up to 3s for confirmation
                time.sleep(0.5)
                new_label = button.text.strip().lower()
                if "booked" in new_label:
                    return "booked"
                if "waitlisted" in new_label:
                    return "waitlisted"
            return ""  # network failed — retry
        return ""
