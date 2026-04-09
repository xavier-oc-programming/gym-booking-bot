# Gym Booking Bot

Selenium bot that automatically books Tuesday and Thursday 6 PM gym classes on the Snack & Lift practice site.

Point the bot at the Snack & Lift gym site (`appbrewery.github.io/gym/`), give it your login credentials, and it scans the weekly class schedule, finds every Tuesday and Thursday 6:00 PM session, and clicks "Book Class" or "Join Waitlist" for each one — printing a full summary of what was booked, what was waitlisted, and what was already reserved. Run it on Monday morning and your whole week is sorted before breakfast.

There are two builds. The **original** build is a single-file procedural script (Step 9 of the course exercise) that uses hardcoded credentials and demonstrates the complete booking flow including admin-panel network simulation and a retry wrapper. The **advanced** build restructures the same logic into three OOP modules — `GymBrowser` for driver management, `ClassBooker` for finding and booking classes — with constants in `config.py`, credentials in `.env`, and headless mode for CI. Both builds produce identical results; the original shows the raw mechanics, the advanced shows how to structure it for production.

This project targets a course practice site, so no real gym account or subscription is required.

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Builds Comparison](#2-builds-comparison)
3. [Usage](#3-usage)
4. [Data Flow](#4-data-flow)
5. [Features](#5-features)
6. [Navigation Flow](#6-navigation-flow)
7. [Architecture](#7-architecture)
8. [Module Reference](#8-module-reference)
9. [Configuration Reference](#9-configuration-reference)
10. [Data Schema](#10-data-schema)
11. [Environment Variables](#11-environment-variables)
12. [Design Decisions](#12-design-decisions)
13. [Course Context](#13-course-context)
14. [Dependencies](#14-dependencies)

---

## 1. Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in ACCOUNT_EMAIL and ACCOUNT_PASSWORD
python menu.py         # select 1 (original) or 2 (advanced)
```

Or run a build directly:

```bash
python original/main.py
python advanced/main.py
```

---

## 2. Builds Comparison

| Feature | Original | Advanced |
|---|---|---|
| File count | 1 | 4 |
| Structure | Procedural, top-to-bottom | OOP — `GymBrowser` + `ClassBooker` |
| Credentials | Hardcoded in script | `.env` / environment variables |
| Path handling | `os.getcwd()` | `Path(__file__).parent` |
| Headless mode | No | Yes (via `HEADLESS` env var) |
| CI-ready | No | Yes (GitHub Actions workflow) |
| Retry logic | Standalone `retry()` function | `retry()` in `config.py` |
| Constants | Inline | Grouped in `config.py` |
| Admin simulation | Yes | Yes |
| Booking verification | Yes | Yes |

---

## 3. Usage

### Original build

```bash
python original/main.py
```

Expected output:

```
Admin login succeeded on attempt 1.
Network simulation enabled.
Failure rate set to 50%.
Cleared all bookings (alert accepted).
Time reset to real time.
Logged out successfully.

Admin setup complete. Network is now flaky.

User login succeeded on attempt 2.
Found 2 Tue/Thu 6:00 PM class(es) to process.
Booking class 1 succeeded on attempt 1.
Booking class 2 failed on attempt 1: TimeoutException. Retrying...
Booking class 2 succeeded on attempt 3.

Finished attempting to book/waitlist 2 class(es).
My Bookings loaded — 2 booked, 0 waitlisted (total 2).

Resilient run complete. Inspect the browser to confirm results.
```

### Advanced build

```bash
# Set credentials first
cp .env.example .env
# Edit .env: ACCOUNT_EMAIL=... ACCOUNT_PASSWORD=...

python advanced/main.py
```

Headless mode (for CI or no-display environments):

```bash
HEADLESS=true python advanced/main.py
```

---

## 4. Data Flow

```
Input:  ACCOUNT_EMAIL, ACCOUNT_PASSWORD (from .env / environment)
   ↓
Browser: GymBrowser opens Chrome, navigates to GYM_URL
   ↓
Auth: login() submits credentials → waits for schedule-page element
   ↓
Admin phase: logs in as admin, enables network simulation (50% failure rate),
             clears previous bookings, resets time, logs out
   ↓
User phase: logs in as user account
   ↓
Scrape: get_class_cards() returns all div[id^='class-card-'] elements
   ↓
Filter: ClassBooker.find_target_cards() keeps only Tue/Thu 6:00 PM cards
   ↓
Book: ClassBooker.book_card() reads button text, clicks "Book Class" or
      "Join Waitlist", returns status string
   ↓
Retry: config.retry() wraps each booking attempt; retries up to 7× on
       network failures or TimeoutException
   ↓
Verify: open_my_bookings() navigates to My Bookings tab, reads booking
        and waitlist card counts
   ↓
Output: console summary — counts of booked, waitlisted, already-reserved
```

---

## 5. Features

### Both builds

**Automated login** — clicks the Login button, fills in email and password, waits for the schedule page to confirm success. Chrome's password-breach popup is suppressed via `credentials_enable_service`, `password_manager_enabled`, and `password_manager_leak_detection` prefs so it never interrupts the run.

**Smart booking** — reads the button label before clicking: "Book Class" → book, "Join Waitlist" → join waitlist, "Booked"/"Waitlisted" → already handled.

**Tue/Thu 6 PM targeting** — scans all class cards, traverses XPath to the parent day-group heading, and filters to Tuesday and Thursday 6:00 PM sessions only.

**Admin network simulation** — logs in as admin, enables 50% network failure simulation, and clears previous bookings to create a clean test environment before the user booking run.

**Retry wrapper** — wraps every action in a configurable retry loop (7 attempts by default, 0.5 s between retries) that catches `NoSuchElementException`, `TimeoutException`, and `WebDriverException`.

**Booking verification** — navigates to My Bookings after booking and reports the confirmed booking and waitlist counts.

**Persistent Chrome profile** — reuses the same browser profile across runs so sessions, cookies, and preferences are preserved.

### Advanced only

**OOP design** — `GymBrowser` owns the driver; `ClassBooker` owns the booking logic. Each is independently testable and swappable.

**`config.py` single source of truth** — every constant (URL, target days/time, timeouts, retry counts) is defined once and imported where needed.

**`.env` credentials** — `ACCOUNT_EMAIL` and `ACCOUNT_PASSWORD` are loaded from `.env`; never hardcoded.

**Headless mode** — set `HEADLESS=true` (env var) to run without a visible browser window; required for CI.

**GitHub Actions workflow** — scheduled Monday 07:00 CET run plus `workflow_dispatch` for manual triggers.

**Context manager** — `GymBrowser` supports `with` syntax for automatic teardown.

---

## 6. Navigation Flow

### a) Terminal menu tree

```
python menu.py
│
├── 1 → python original/main.py
│         (runs in original/ as cwd)
│         Press Enter to return to menu
│
├── 2 → python advanced/main.py
│         (runs in advanced/ as cwd)
│         Press Enter to return to menu
│
└── q → exit
```

### b) Execution flow

```
Start
 │
 ├─ Open Chrome with persistent profile
 │
 ├─ ADMIN PHASE
 │   ├─ navigate to GYM_URL
 │   ├─ login(ADMIN_EMAIL, ADMIN_PASSWORD)
 │   │   ├─ network error → retry (up to 7×)
 │   │   └─ success → schedule-page present
 │   ├─ enable network simulation (50% failure rate)
 │   ├─ clear all bookings
 │   ├─ reset time to real time
 │   └─ logout()
 │
 ├─ USER PHASE
 │   ├─ login(ACCOUNT_EMAIL, ACCOUNT_PASSWORD)
 │   │   ├─ network error → retry (up to 7×)
 │   │   └─ success → schedule-page present
 │   ├─ get_class_cards() → all div[id^='class-card-'] elements
 │   ├─ find_target_cards() → filter Tue/Thu + 6:00 PM
 │   └─ for each target card:
 │       ├─ book_card()
 │       │   ├─ "Book Class"     → click → return "booked"
 │       │   ├─ "Join Waitlist"  → click → return "waitlisted"
 │       │   ├─ "Booked"         → return "already_booked"
 │       │   └─ "Waitlisted"     → return "already_waitlisted"
 │       └─ network error → retry (up to 7×)
 │
 ├─ VERIFICATION PHASE
 │   ├─ open My Bookings tab
 │   ├─ wait 5 s for React state update
 │   ├─ re-click tab to refresh data
 │   ├─ count booking-card-* and waitlist-card-* elements
 │   └─ print summary
 │
 └─ End (browser stays open for inspection in non-headless mode)
```

---

## 7. Architecture

```
gym-booking-bot/
│
├── menu.py                    # entry point — prints LOGO, launches builds
├── art.py                     # LOGO ASCII art
├── requirements.txt           # pip dependencies + Python version note
├── .env.example               # credential placeholders (committed)
├── .env                       # real credentials (gitignored)
├── .gitignore
│
├── docs/
│   └── COURSE_NOTES.md        # course exercise description, step breakdown
│
├── original/
│   └── main.py                # Step 9 verbatim — resilient booking bot
│                              #   chrome_profile/ path fixed to Path(__file__).parent
│
├── advanced/
│   ├── config.py              # all constants + retry() helper
│   ├── browser.py             # GymBrowser — Chrome setup, login, logout, navigation
│   ├── booker.py              # ClassBooker — find target cards, book each one
│   └── main.py                # orchestrator — wires GymBrowser + ClassBooker
│
└── .github/
    └── workflows/
        └── gym-booking-bot.yml  # Monday 07:00 CET schedule + workflow_dispatch
```

---

## 8. Module Reference

### `GymBrowser` (`advanced/browser.py`)

| Method | Returns | Description |
|---|---|---|
| `__init__(headless)` | — | Creates Chrome WebDriver with persistent profile; headless if `HEADLESS=true` |
| `__enter__` / `__exit__` | — | Context manager — calls `quit()` on exit |
| `open_gym()` | `None` | Navigates to `GYM_URL` |
| `login(email, password)` | `bool` | Logs in; returns `True` on success, `False` on network-failure banner |
| `logout()` | `None` | Clicks logout button if present; silent if already logged out |
| `wait_for_schedule()` | `None` | Blocks until `#schedule-page` is in the DOM |
| `get_class_cards()` | `list[WebElement]` | Returns all `div[id^='class-card-']` elements after schedule loads |
| `open_my_bookings()` | `tuple[int, int]` | Opens My Bookings tab, waits for refresh; returns `(booked, waitlisted)` |
| `quit()` | `None` | Quits the WebDriver session |

### `ClassBooker` (`advanced/booker.py`)

| Method | Returns | Description |
|---|---|---|
| `__init__(browser)` | — | Stores reference to an authenticated `GymBrowser` |
| `find_target_cards(target_days, target_time)` | `list[WebElement]` | Filters schedule cards to those matching `target_days` and `target_time` |
| `book_card(card)` | `str` | Clicks book/waitlist button; returns `"booked"`, `"waitlisted"`, `"already_booked"`, `"already_waitlisted"`, or `"unknown:<text>"` |

---

## 9. Configuration Reference

All constants are in `advanced/config.py`.

| Constant | Default | Description |
|---|---|---|
| `GYM_URL` | `"https://appbrewery.github.io/gym/"` | Target gym website URL |
| `TARGET_DAYS` | `("Tue", "Thu")` | Day abbreviations to match in day-group h2 headers |
| `TARGET_TIME` | `"6:00 PM"` | Time string to match in `class-time-*` elements |
| `WAIT_TIMEOUT` | `5` | Seconds for `WebDriverWait` explicit waits |
| `HEADLESS` | `False` | Read from `HEADLESS` env var; set `true` for CI |
| `DEFAULT_RETRIES` | `7` | Max retry attempts per action |
| `RETRY_DELAY` | `0.5` | Seconds to sleep between retry attempts |
| `ADMIN_EMAIL` | `"admin@test.com"` | Admin account for the practice site |
| `ADMIN_PASSWORD` | `"admin123"` | Admin password for the practice site |
| `CHROME_PROFILE_DIR` | `advanced/chrome_profile/` | Persistent Chrome profile directory |

---

## 10. Data Schema

### Class card structure (DOM)

The gym site uses consistent ID patterns that the bot relies on:

```
div[id^="day-group-"]          ← day section container
  h2                           ← day title, e.g. "Tue, Nov 11"
  div[id^="class-card-"]       ← one card per class
    h3[id^="class-name-"]      ← class name, e.g. "Spin Class"
    p[id^="class-time-"]       ← time string, e.g. "Time: 6:00 PM"
    button[id^="book-button-"] ← state: "Book Class" | "Join Waitlist"
                               #          | "Booked" | "Waitlisted"
```

### `book_card()` return values

| Return value | Meaning |
|---|---|
| `"booked"` | Button was "Book Class" — clicked successfully |
| `"waitlisted"` | Button was "Join Waitlist" — clicked successfully |
| `"already_booked"` | Button was "Booked" — no action needed |
| `"already_waitlisted"` | Button was "Waitlisted" — no action needed |
| `"unknown:<text>"` | Unrecognised button state |

### `open_my_bookings()` return value

```python
(booked_count: int, waitlisted_count: int)
# e.g. (2, 0) → 2 confirmed bookings, 0 on waitlist
```

---

## 11. Environment Variables

Copy `.env.example` to `.env` and fill in values.

| Variable | Required | Description |
|---|---|---|
| `ACCOUNT_EMAIL` | Yes | Email address of your gym site account |
| `ACCOUNT_PASSWORD` | Yes | Password for your gym site account |
| `HEADLESS` | No | Set to `"true"` to run Chrome headlessly (default: `"false"`) |

---

## 12. Design Decisions

**`config.py` zero magic numbers** — every URL, timeout, retry count, and target schedule value is defined once in `config.py`. Changing the target time from 6 PM to 7 PM means editing one line.

**Separate `GymBrowser` / `ClassBooker` modules** — each is testable in isolation. Swap the driver setup (e.g., Firefox, remote WebDriver) without touching the booking logic. Swap the booking algorithm without touching the browser setup.

**`retry()` in `config.py`** — it is a pure function whose only inputs are constants defined in the same file (`DEFAULT_RETRIES`, `RETRY_DELAY`). Placing it next to the data it operates on keeps the two in sync.

**Credentials via `.env`, never hardcoded** — environment variables are the security baseline for any credential. The original build uses hardcoded values because it's a course exercise targeting a demo site; the advanced build uses `.env` as the correct pattern.

**`.env.example` committed, `.env` gitignored** — documents the required variables without leaking real values. Anyone cloning the repo knows exactly what to fill in.

**`Path(__file__).parent` for all file paths** — `os.getcwd()` breaks when the script is launched from a different directory (e.g., via `menu.py` with `cwd=`). `__file__` is always the script's own location.

**`sys.path.insert` pattern** — `advanced/main.py` and its siblings insert their own directory at the front of `sys.path` so imports work whether the script is launched from `menu.py` or run directly.

**`subprocess.run` + `cwd=`** — `menu.py` launches each build as a subprocess with `cwd` set to the build's own directory. This ensures relative imports inside the build resolve correctly.

**`while True` in `menu.py` vs recursion** — the menu re-draws by looping, never by calling itself. No stack growth regardless of how many times the user runs builds.

**Console cleared before every valid menu render** — the `clear` flag prevents clearing after invalid input so the error message stays visible. Clears after a subprocess returns so the menu is always clean.

**`input/ output/ data/` directories omitted** — this bot produces no output files and persists no state between runs beyond the Chrome profile (which is gitignored). Adding empty directories would be noise.

**`detach=True` in non-headless mode** — keeps the browser open after the script exits so you can visually inspect the result. Headless mode omits this (the process exits cleanly for CI).

**`try/except` per booking, not around the whole loop** — if one class fails after all retries, the others still get booked. The retry wrapper raises only after exhausting all attempts.

**Chrome password-breach popup suppressed via prefs** — `password123` is a known breached password; Chrome would normally show a blocking "Change your password" dialog mid-run. Setting `credentials_enable_service`, `profile.password_manager_enabled`, and `profile.password_manager_leak_detection` to `False` in ChromeOptions prefs prevents it entirely. A `--disable-features` flag would also work but prefs are more targeted.

---

## 13. Course Context

Built as Day 49 of [100 Days of Code: The Complete Python Pro Bootcamp](https://www.udemy.com/course/100-days-of-code/) by Dr. Angela Yu.

**Concepts covered in the original build:**
- Selenium WebDriver and `ChromeOptions`
- Persistent Chrome profiles (`--user-data-dir`)
- Explicit waits: `WebDriverWait` and `expected_conditions`
- CSS selector patterns (`div[id^='class-card-']`)
- XPath ancestor traversal (`./ancestor::div[...]`)
- Button state inspection and conditional booking
- Admin panel automation (time simulation, network simulation)
- Retry wrapper with configurable attempts
- Exception handling: `NoSuchElementException`, `TimeoutException`, `WebDriverException`

**The advanced build extends into:**
- OOP design with single-responsibility classes
- `config.py` as a constants module with a co-located helper
- Credentials management with `python-dotenv`
- Headless browser operation for CI environments
- GitHub Actions scheduling

See [docs/COURSE_NOTES.md](docs/COURSE_NOTES.md) for the full step-by-step breakdown.

---

## 14. Dependencies

| Module | Used in | Purpose |
|---|---|---|
| `selenium` | Both builds | WebDriver API — launching Chrome, finding elements, clicking |
| `python-dotenv` | Advanced | Load `ACCOUNT_EMAIL` / `ACCOUNT_PASSWORD` from `.env` |
| `pathlib.Path` | Both builds | Resolve file paths relative to `__file__` |
| `os` | Both builds | `makedirs` for Chrome profile directory |
| `time` | Both builds | `sleep` between retry attempts and after logout |
