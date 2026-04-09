import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
CHROME_PROFILE_DIR = BASE_DIR / "chrome_profile"

# ---------------------------------------------------------------------------
# URLs
# ---------------------------------------------------------------------------
GYM_URL = "https://appbrewery.github.io/gym/"

# ---------------------------------------------------------------------------
# Target schedule
# ---------------------------------------------------------------------------
TARGET_DAYS = ("Tue", "Thu")   # day abbreviations as shown in the site's h2 headers
TARGET_TIME = "6:00 PM"        # time string as shown in class-time-* elements

# ---------------------------------------------------------------------------
# Browser
# ---------------------------------------------------------------------------
WAIT_TIMEOUT = 5               # seconds for WebDriverWait explicit waits
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"  # set HEADLESS=true for CI

# ---------------------------------------------------------------------------
# Retry / resilience
# ---------------------------------------------------------------------------
DEFAULT_RETRIES = 7
RETRY_DELAY = 0.5              # seconds to sleep between retry attempts

# ---------------------------------------------------------------------------
# Admin (for QA / time-simulation testing only)
# ---------------------------------------------------------------------------
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "admin123"


def retry(func, retries: int = DEFAULT_RETRIES, description: str = None):
    """
    Retry *func* up to *retries* times.
    Retries on any Exception or on a falsy return value.
    Returns the first truthy result, or None after exhausting all attempts.
    """
    import time
    from selenium.common.exceptions import (
        NoSuchElementException,
        TimeoutException,
        WebDriverException,
        UnexpectedAlertPresentException,
    )

    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            result = func()
            if result:
                if description:
                    print(f"{description} succeeded on attempt {attempt}.")
                return result
            print(f"{description or 'Operation'} returned falsy on attempt {attempt}, retrying...")
        except (NoSuchElementException, TimeoutException, WebDriverException,
                UnexpectedAlertPresentException) as exc:
            last_exc = exc
            print(f"{description or 'Operation'} failed on attempt {attempt}: "
                  f"{exc.__class__.__name__}. Retrying...")
            time.sleep(RETRY_DELAY)
    print(f"{description or 'Operation'} failed after {retries} attempts.")
    if last_exc:
        raise last_exc
    return None
