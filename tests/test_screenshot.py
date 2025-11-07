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
VIEWPORTS = config.get("viewports", [{"width": 1920, "height": 1080, "name": "default"}])
SCREENSHOT_MODE = config.get("screenshot_mode", "old")  # 'old' or 'new'

# -----------------------------
# Screenshot folders
# -----------------------------
BASE_SCREENSHOT_DIR = os.path.join(PROJECT_ROOT, f"screenshots/{SCREENSHOT_MODE}")
DIFF_DIR = os.path.join(PROJECT_ROOT, "screenshots/diff")
os.makedirs(BASE_SCREENSHOT_DIR, exist_ok=True)
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
# Helper: set language cookie
# -----------------------------
def set_language_cookie(context, route):
    """Detect language from route and set cookie accordingly."""
    domain = "playwright.dev"

    if route.startswith("/python/"):
        lang = "python"
    elif route.startswith("/java/"):
        lang = "java"
    elif route.startswith("/dotnet/"):
        lang = "dotnet"
    else:
        lang = "nodejs"  # Default for docs without prefix

    try:
        context.add_cookies([
            {"name": "preferredLang", "value": lang, "domain": domain, "path": "/"}
        ])
        print(f"🌐 Language set to: {lang} for route: {route}")
    except Exception as e:
        print(f"⚠️ Failed to set language cookie for {route}: {e}")


# -----------------------------
# Test: Take screenshots (multi-viewport)
# -----------------------------
def test_take_screenshots():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)

        for vp in VIEWPORTS:
            name = vp.get("name", f"{vp['width']}x{vp['height']}")
            viewport_dir = os.path.join(BASE_SCREENSHOT_DIR, name)
            os.makedirs(viewport_dir, exist_ok=True)

            print(f"\n🖥️  Viewport: {name} ({vp['width']}x{vp['height']})")

            for route in ROUTES:
                # ✅ Detect and set correct language before creating context
                domain = "playwright.dev"

                if route.startswith("/python/"):
                    lang = "python"
                elif route.startswith("/java/"):
                    lang = "java"
                elif route.startswith("/dotnet/"):
                    lang = "dotnet"
                else:
                    lang = "nodejs"

                # Create new isolated context for this route
                context = browser.new_context(
                    viewport={"width": vp["width"], "height": vp["height"]}
                )

                # Add the cookie BEFORE any page is created
                context.add_cookies([
                    {"name": "preferredLang", "value": lang, "domain": domain, "path": "/"}
                ])
                print(f"🌐 Language set to: {lang} for route: {route}")

                # Now create page inside this context
                page = context.new_page()
                base = BasePage(page)

                url = BASE_URL + route
                filename = route.strip("/").replace("/", "_") or "home"
                filename = filename.rstrip("_") + ".png"
                screenshot_path = os.path.join(viewport_dir, filename)

                print(f"[{SCREENSHOT_MODE.upper()}] Taking screenshot: {url} → {screenshot_path}")

                try:
                    # Navigate and wait for full load
                    base.goto(url)
                    page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(1000)

                    # Optional button click
                    continue_button = BUTTONS.get("continue_button_name")
                    if continue_button:
                        try:
                            page.get_by_role("button", name=continue_button).click(timeout=2000)
                            page.wait_for_timeout(500)
                        except:
                            print(f"Button '{continue_button}' not found on {url}")

                    # Scroll for lazy load
                    if SCROLL_TO_LOAD:
                        try:
                            scroll_to_bottom(page)
                            page.wait_for_timeout(1000)
                        except Exception as e:
                            print(f"⚠️ Scroll failed on {url}: {e}")

                    # Full page screenshot
                    base.take_screenshot(screenshot_path)

                except Exception as e:
                    print(f"❌ Error on {url}: {e}")

                # Close context after each route
                context.close()

        browser.close()



# -----------------------------
# Test: Compare screenshots across all viewports
# -----------------------------
def test_compare_screenshots():
    old_dir = os.path.join(PROJECT_ROOT, "screenshots/old")
    new_dir = os.path.join(PROJECT_ROOT, "screenshots/new")

    print("\n📸 Comparing screenshots for all viewports...")
    total_diffs = 0

    for vp in VIEWPORTS:
        name = vp.get("name", f"{vp['width']}x{vp['height']}")
        old_vp_dir = os.path.join(old_dir, name)
        new_vp_dir = os.path.join(new_dir, name)
        vp_diff_dir = os.path.join(DIFF_DIR, name)
        os.makedirs(vp_diff_dir, exist_ok=True)

        if not os.path.exists(old_vp_dir) or not os.path.exists(new_vp_dir):
            print(f"⚠️ Skipping viewport '{name}' — screenshots missing.")
            continue

        print(f"\n🔍 Comparing viewport: {name}")
        results = batch_compare(old_vp_dir, new_vp_dir, vp_diff_dir)
        different_files = [f for f, same in results.items() if not same]

        print(f"  Total compared: {len(results)}")
        print(f"  Differences: {len(different_files)}")

        if different_files:
            total_diffs += len(different_files)
            print("  ⚠️ Differences found:")
            for file in different_files:
                print(f"   - {file}")

    assert total_diffs == 0, f"❌ {total_diffs} visual differences found! Check {DIFF_DIR}."
    print("✅ All screenshots match across viewports.")
