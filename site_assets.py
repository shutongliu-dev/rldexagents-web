"""Shared local head assets for the standalone project pages."""
import re
FAVICON_LINKS = (
    '<link rel="icon" href="favicon.ico?v=1" sizes="any">'
    '<link rel="icon" type="image/png" sizes="32x32" href="assets/favicon-32.png?v=1">'
    '<link rel="apple-touch-icon" sizes="180x180" href="assets/favicon-180.png">'
)


def add_site_icons(page):
    page = re.sub(r'href="assets/rldex_report.css(?:\?[^\"]*)?"', 'href="assets/rldex_report.css?v=simulation-1"', page)
    if 'favicon.ico' not in page:
        page = page.replace('</head>', FAVICON_LINKS + '</head>', 1)
    return page
