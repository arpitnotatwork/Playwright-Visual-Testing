from urllib.parse import urljoin, urlparse

class LinkCheckerPage:
    def __init__(self, page, base_url):
        self.page = page
        self.base_url = base_url

    def get_all_links(self):
        """Extract all <a> hrefs safely as strings."""
        anchors = self.page.query_selector_all("a[href]")
        links = []
        for a in anchors:
            href = a.get_attribute("href")
            if href and isinstance(href, str):
                links.append(href)
        return list(set(links))

    def is_valid_link(self, href, base_url, skip_domains):
        """
        Validates if a link should be tested.
        Skips:
        - empty or anchor-only links (#)
        - mailto:, tel:, javascript:
        - links to domains in skip_domains
        - external links (not same domain as base_url)
        """
        if not href or href.startswith("#"):
            return False

        href_lower = href.lower()

        # Skip mailto, tel, and javascript links
        if href_lower.startswith(("mailto:", "tel:", "javascript:")):
            return False

        # Skip explicitly configured domains
        if any(skip in href_lower for skip in skip_domains):
            return False

        # Only allow internal links (same domain)
        base_domain = urlparse(base_url).netloc
        link_domain = urlparse(href).netloc

        # If the link domain is empty (relative path), it's internal
        # If it matches base domain, also internal
        if link_domain and link_domain != base_domain:
            return False

        return True

    def get_full_link(self, href):
        """Convert relative links to absolute URLs."""
        if href.startswith("http"):
            return href
        return urljoin(self.base_url, href)



