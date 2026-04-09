"""
booker.py — class ClassBooker

Finds target class cards and books / joins the waitlist for each one.
Pure logic — no driver setup, no print summaries, no file I/O.
Raises exceptions on failure; does NOT call sys.exit().
"""

import sys
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
        cards = self._browser.get_class_cards()
        results = []
        for card in cards:
            day_group = card.find_element(
                By.XPATH, "./ancestor::div[contains(@id, 'day-group-')]"
            )
            day_title = day_group.find_element(By.TAG_NAME, "h2").text
            if any(day in day_title for day in target_days):
                time_text = card.find_element(
                    By.CSS_SELECTOR, "p[id^='class-time-']"
                ).text
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
            "already_waitlisted", or "unknown:<button_text>".
        """
        button = card.find_element(By.CSS_SELECTOR, "button[id^='book-button-']")
        label = button.text.strip().lower()

        if "book class" in label:
            button.click()
            return "booked"
        if "join waitlist" in label:
            button.click()
            return "waitlisted"
        if "booked" in label:
            return "already_booked"
        if "waitlisted" in label:
            return "already_waitlisted"
        return f"unknown:{button.text.strip()}"
