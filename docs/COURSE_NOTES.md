# Day 49 — Course Notes

## Exercise Description

Build a Selenium automation bot that logs in to the Snack & Lift gym practice
site (`appbrewery.github.io/gym/`) and books all available Tuesday and Thursday
6:00 PM classes. The bot must handle the case where a class is already booked,
full (waitlist), or unavailable, and provide a summary of all actions taken.

The course was structured as a step-by-step progression:

| File | What it introduces |
|---|---|
| `0)_Day49_Goals.py` | Day outline (empty placeholder) |
| `1)_Step1_...` | ChromeOptions, persistent profile, detach mode, basic navigation |
| `2)_Step2_...` | WebDriverWait, explicit waits, automated login |
| `3)_Step3_...` | CSS selector patterns, XPath ancestor traversal, booking a single class |
| `4)_Step4_...` | Button state detection (Book / Waitlist / Booked / Waitlisted) |
| `5)_Step5_...` | Action counters and console summary |
| `6)_Step6_...` | Extending the filter to Tuesday **and** Thursday |
| `7)_Step7_...` | Navigating to "My Bookings" page to verify bookings |
| `8)_Step8_...` | Admin panel — time simulation (+3 days) for QA/testing |
| `9)_Step9_...` | Network failure simulation, retry wrapper, resilience ← **used as original/main.py** |

## Credentials Note

The course files contain hardcoded credentials for the practice site
(`appbrewery.github.io/gym/`). These are demo credentials for a fictional gym
website with no real user data. They are **not** credentials for any real
service and pose no security risk.

The advanced build uses `.env` / environment variables for credentials.

## Concepts Covered (Original Build)

- Selenium WebDriver setup with `ChromeOptions`
- Persistent Chrome profile (`--user-data-dir`)
- Explicit waits (`WebDriverWait`, `expected_conditions`)
- CSS selector patterns (`div[id^='class-card-']`)
- XPath ancestor traversal (`./ancestor::div[contains(@id, ...)]`)
- Button state inspection and conditional booking logic
- Admin panel automation (time simulation, network failure simulation)
- Retry wrapper with configurable attempts and delay
- Exception handling: `NoSuchElementException`, `TimeoutException`,
  `WebDriverException`, `UnexpectedAlertPresentException`

## Advanced Build Extensions

- OOP design: `GymBrowser` (driver management) + `ClassBooker` (booking logic)
- `config.py` as single source of truth for all constants
- Credentials via `.env` / `python-dotenv` (never hardcoded)
- Headless Chrome support via `HEADLESS` env var (for CI)
- GitHub Actions workflow for scheduled / manual runs
- `Path(__file__).parent` for all file paths
