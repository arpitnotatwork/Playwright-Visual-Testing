import os
import sys
import yaml
import pytest
from playwright.sync_api import sync_playwright
from pages.base_page import BasePage
from utils.image_compare import batch_compare

# -----------------------------
# Project root setup
# -----------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# -----------------------------
# Load config
# -----------------------------
with open(os.path.join(PROJECT_ROOT, "config.yaml")) as f:
    config = yaml.safe_load(f)

BASE_URL = config["base_url"]
ROUTES = config["routes"]
BUTTONS = config.get("buttons", {})
HEADLESS = config.get("headless", True)
SCROLL_TO_LOAD = config.get("scroll_to_load", True)

# -----------------------------
# Screenshot folders
# -----------------------------
SCREENSHOT_MODE = config.get("screenshot_mode", "new")  # 'old' or 'new'
SCREENSHOT_DIR = os.path.join(PROJECT_ROOT, f"screenshots/{SCREENSHOT_MODE}")
DIFF_DIR = os.path.join(PROJECT_ROOT, "screenshots/diff")

os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(DIFF_DIR, exist_ok=True)


# -----------------------------
# Helper: smooth scroll to bottom
# -----------------------------
def scroll_to_bottom(page):
    page.evaluate(
        """
        let totalHeight = 0;
        const distance = 500;
        const delay = 100;
        return new Promise((resolve) => {
            const timer = setInterval(() => {
                window.scrollBy(0, distance);
                totalHeight += distance;
                if (totalHeight >= document.body.scrollHeight - window.innerHeight) {
                    clearInterval(timer);
                    resolve();
                }
            }, delay);
        });
        """
    )


# -----------------------------
# Test: Take screenshots
# -----------------------------
def test_take_screenshots():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        page = browser.new_page()
        base = BasePage(page)

        for route in ROUTES:
            url = BASE_URL + route
            filename = route.strip("/").replace("/", "_") or "home"
            filename = filename.rstrip("_") + ".png"
            screenshot_path = os.path.join(SCREENSHOT_DIR, filename)

            print(f"[{SCREENSHOT_MODE.upper()}] Taking screenshot: {url} → {screenshot_path}")

            # Navigate
            base.goto(url)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(1000)

            # Optional "Continue" or cookie button click
            continue_button = BUTTONS.get("continue_button_name")
            if continue_button:
                try:
                    page.get_by_role("button", name=continue_button).click(timeout=2000)
                    page.wait_for_timeout(500)
                except:
                    print(f"Button '{continue_button}' not found on {url}")

            # Scroll to bottom (for lazy content)
            if SCROLL_TO_LOAD:
                try:
                    scroll_to_bottom(page)
                    page.wait_for_timeout(1000)
                except Exception as e:
                    print(f"⚠️ Scroll failed on {url}: {e}")

            # Take full-page screenshot
            base.take_screenshot(screenshot_path)

        browser.close()


# -----------------------------
# Test: Compare screenshots
# -----------------------------
def test_compare_screenshots():
    old_dir = os.path.join(PROJECT_ROOT, "screenshots/old")
    new_dir = os.path.join(PROJECT_ROOT, "screenshots/new")

    results = batch_compare(old_dir, new_dir, DIFF_DIR)
    different_files = [f for f, same in results.items() if not same]

    print("\n📊 Screenshot Comparison Summary")
    print("---------------------------------")
    print(f"Total compared: {len(results)}")
    print(f"Different: {len(different_files)}")

    if different_files:
        print("\n⚠️ Differences found:")
        for file in different_files:
            print(f" - {file}")

    missing_in_new = [f for f in os.listdir(old_dir) if f not in results]
    for file in missing_in_new:
        print(f"❌ Missing in new screenshots: {file}")

    assert not different_files, f"{len(different_files)} differences found! Check {DIFF_DIR}."
