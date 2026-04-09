import os
import sys
import subprocess
from pathlib import Path

from art import LOGO

ORIGINAL = Path(__file__).parent / "original" / "main.py"
ADVANCED = Path(__file__).parent / "advanced" / "main.py"


def main():
    clear = True
    while True:
        if clear:
            os.system("cls" if os.name == "nt" else "clear")
        clear = True

        print(LOGO)
        print("Gym Booking Bot — pick a build:\n")
        print("  1. Original  (course file, Step 9 — resilient booking bot)")
        print("  2. Advanced  (OOP build — config, browser, booker modules)")
        print("  q. Quit\n")

        choice = input("Choice: ").strip().lower()

        if choice == "1":
            subprocess.run([sys.executable, str(ORIGINAL)], cwd=str(ORIGINAL.parent))
            input("\nPress Enter to return to menu...")
        elif choice == "2":
            subprocess.run([sys.executable, str(ADVANCED)], cwd=str(ADVANCED.parent))
            input("\nPress Enter to return to menu...")
        elif choice == "q":
            break
        else:
            print("Invalid choice. Try again.")
            clear = False


if __name__ == "__main__":
    main()
