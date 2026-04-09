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
| `1)_Step1_Setup_Chrome_Profile_and_Basic_Navigation.py` | ChromeOptions, persistent profile, detach mode, basic navigation |
| `2)_Step2_Automated_Login.py` | WebDriverWait, explicit waits, automated login |
| `3)_Step3_Book_the_upcoming_Tuesday_class.py` | CSS selector patterns, XPath ancestor traversal, booking a single class |
| `4)_Step4_Check_if_a_class_is_already_booked.py` | Button state detection (Book / Waitlist / Booked / Waitlisted) |
| `5)_Step5_Add_counters_to_your_script_to_provide_a_neat_summary.py` | Action counters and console summary |
| `6)_Step6_Class_Booking_Book_every_Tuesday_and_Thursday_class.py` | Extending the filter to Tuesday **and** Thursday |
| `7)_Step7_Verify_Class_bookings_on_the_My_Bookings_Page.py` | Navigating to "My Bookings" page to verify bookings |
| `8)_Step8_Time_Travel_Quality_Assurance_QA.py` | Admin panel — time simulation (+3 days) for QA/testing |
| `9)_Step9_Add_Resilience_in_case_of_Network_Failures.py` | Network failure simulation, retry wrapper, resilience ← **used as original/main.py** |

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
