"""Shared local head assets for the standalone project pages."""
import re
FAVICON_LINKS = (
    '<link rel="icon" href="favicon.ico?v=1" sizes="any">'
    '<link rel="icon" type="image/png" sizes="32x32" href="assets/favicon-32.png?v=1">'
    '<link rel="apple-touch-icon" sizes="180x180" href="assets/favicon-180.png">'
)


def add_site_icons(page):
    page = re.sub(r'href="assets/rldex_report.css(?:\?[^\"]*)?"', 'href="assets/rldex_report.css?v=demo-note-1"', page)
    if 'favicon.ico' not in page:
        page = page.replace('</head>', FAVICON_LINKS + '</head>', 1)
    return apply_project_titles(page)


PROJECT_SUBTITLE = 'Learning and Refining Dexterous Manipulation Skills through Interaction'
PROJECT_DESCRIPTION = 'From Motion Representations to Executable Dexterous Skills and Agentic Manipulation'


def apply_project_titles(page):
    """Keep project headings consistent across report and interactive pages."""
    page = re.sub(r'<title>.*?</title>', '<title>DexSkill — ' + PROJECT_SUBTITLE + '</title>', page, count=1, flags=re.S)
    # Replace an existing title group, including earlier applications of this helper.
    page = re.sub(r'<h3 class="project-subtitle">.*?</h3>\s*<p class="project-description">.*?</p>', '', page, flags=re.S)
    page = re.sub(r'<div class="sub-hero-text">.*?</div>\s*<p class="report-subtitle">.*?</p>', '', page, count=1, flags=re.S)
    heading = '<h3 class="project-subtitle">' + PROJECT_SUBTITLE + '</h3><p class="project-description"><strong>' + PROJECT_DESCRIPTION + '</strong></p>'
    page = re.sub(r'(<h1\b[^>]*>).*?</h1>', lambda m: m[1] + 'DexSkill</h1>' + heading, page, count=1, flags=re.S)
    page = page.replace('RLDexAgents / Research Supplement', 'DexSkill / Research Supplement')
    if 'href="assets/project-titles.css"' not in page:
        page = page.replace('</head>', '<link rel="stylesheet" href="assets/project-titles.css"></head>', 1)
    return page
