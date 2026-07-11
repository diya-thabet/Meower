import subprocess
import sys

TOOLS = {
    "theHarvester": ["theHarvester", "-h"],
    "sherlock": ["sherlock", "--help"],
    "holehe": ["holehe", "--help"],
    "maigret": ["maigret", "--help"],
    "ghunt": ["ghunt", "--help"],
    "h8mail": ["h8mail", "--help"],
    "instaloader": ["instaloader", "--help"],
    "snscrape": ["snscrape", "--help"],
    "censys": ["censys", "--help"],
    "shodan": ["shodan", "--help"],
    "emailfinder": ["emailfinder", "--help"],
}

all_ok = True
for name, cmd in TOOLS.items():
    try:
        subprocess.run(cmd, capture_output=True, timeout=10)
        print(f"  [OK] {name}")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print(f"  [MISSING] {name}")
        all_ok = False

if all_ok:
    print("\nAll tools are ready!")
else:
    print("\nSome tools are missing. Install them before proceeding.")
    sys.exit(1)
