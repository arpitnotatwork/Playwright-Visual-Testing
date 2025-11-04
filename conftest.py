import os
import yaml
import pytest
from datetime import datetime
from playwright.sync_api import sync_playwright
import sys


PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# ------------------------------
# Load config.yaml safely
# ------------------------------
@pytest.fixture(scope="session")
def config():
    config_path = os.path.join(os.getcwd(), "config.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

# ------------------------------
# Base URL fixture
# ------------------------------
@pytest.fixture(scope="session")
def base_url(config):
    return config.get("base_url", "http://localhost")  # default fallback

# ------------------------------
# Skip domains fixture (optional)
# ------------------------------
@pytest.fixture(scope="session")
def skip_domains(config):
    return config.get("skip_domains", [])  # default empty list if missing

# ------------------------------
# Max pages fixture (optional)
# ------------------------------
@pytest.fixture(scope="session")
def max_pages(config):
    return config.get("max_pages", None)  # default None if missing

# ------------------------------
# Reports folder fixture
# ------------------------------
@pytest.fixture(scope="session")
def create_reports_folder():
    reports_dir = os.path.join(os.getcwd(), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir

# ------------------------------
# Browser context fixture
# ------------------------------
@pytest.fixture(scope="session")
def browser_context():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        yield context
        browser.close()

# ------------------------------
# Page fixture
# ------------------------------
@pytest.fixture()
def page(browser_context):
    page = browser_context.new_page()
    page.set_default_timeout(50000)
    yield page
    page.close()

