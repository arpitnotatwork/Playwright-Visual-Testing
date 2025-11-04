import sys, os
import pytest
import yaml
import requests
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pages.link_checker_page import LinkCheckerPage
from utils.excel_writer import write_results_to_excel

# HTTP code meanings
HTTP_MEANINGS = {
    200: "OK", 301: "Moved Permanently", 302: "Found (Redirect)", 400: "Bad Request",
    401: "Unauthorized", 403: "Forbidden", 404: "Not Found", 500: "Internal Server Error",
    502: "Bad Gateway", 503: "Service Unavailable"
}

# -------------------- Fixtures --------------------
@pytest.fixture(scope="session")
def config():
    with open("config.yaml", "r") as f:
        cfg = yaml.safe_load(f)
    cfg["skip_domains"] = [str(d) for d in cfg.get("skip_domains", [])]
    return cfg

# -------------------- Link checker --------------------
def check_link(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        if response.status_code == 405:  # HEAD not allowed
            response = requests.get(url, allow_redirects=True, timeout=10)
        status = response.status_code
        meaning = HTTP_MEANINGS.get(status, "Unknown Status")
        result = "Pass" if status < 400 else "Fail"
    except requests.RequestException:
        status, meaning, result = "Error", "Connection Error", "Fail"
    return status, meaning, result

# -------------------- Crawl site --------------------
def crawl_site(context, base_url, skip_domains, max_pages, routes=None, config=None):
    visited = set()
    to_visit = [urljoin(base_url, r) for r in (routes or ["/"])]
    results = []

    continue_name = config.get("buttons", {}).get("continue_button_name") if config else None

    while to_visit and len(visited) < max_pages:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue
        visited.add(current_url)

        page = context.new_page()
        try:
            print(f"🔍 Visiting: {current_url}")
            page.goto(current_url, timeout=config.get("timeout", 60000) if config else 60000)
        except Exception as e:
            results.append([current_url, "Page Load Error", "Error", str(e), "Fail"])
            page.close()
            continue

        # Click optional Continue button
        if continue_name:
            try:
                page.get_by_role("button", name=continue_name).click(timeout=5000)
                page.wait_for_timeout(1000)
            except:
                pass  # ignore if button not found

        try:
            link_page = LinkCheckerPage(page, base_url)
            links = link_page.get_all_links()

            for href in links:
                if not link_page.is_valid_link(href, base_url, skip_domains):
                    continue
                full_link = link_page.get_full_link(href)
                status, meaning, result = check_link(full_link)
                results.append([current_url, full_link, status, meaning, result])

                if full_link.startswith(base_url) and full_link not in visited and full_link not in to_visit:
                    to_visit.append(full_link)
        finally:
            page.close()

    print(f"✅ Crawled {len(visited)} pages, found {len(results)} links total.")
    return results

# -------------------- Test --------------------
def test_broken_links_full_crawl(config):
    base_url = config["base_url"]
    skip_domains = config.get("skip_domains", [])
    max_pages = config.get("max_pages", 100)
    routes = config.get("routes") if not config.get("enable_full_crawl", True) else None

    with sync_playwright() as p:
        browser = getattr(p, config.get("browser", "chromium")).launch(headless=True)
        context = browser.new_context()

        results = crawl_site(context, base_url, skip_domains, max_pages, routes, config)
        file_path = write_results_to_excel(results, config.get("report_file"))

        browser.close()

        failed_links = [r for r in results if r[-1] == "Fail"]
        print(f"\n✅ Report saved to: {file_path}")
        print(f"Total links checked: {len(results)}")
        print(f"Failed links: {len(failed_links)}")
        for r in failed_links:
            print(f"{r[0]} → {r[1]} [{r[3]}]")

        assert not failed_links, f"{len(failed_links)} broken links found! See report: {file_path}"
