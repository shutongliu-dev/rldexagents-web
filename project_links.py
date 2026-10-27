"""Public paper/code shortcuts for the project-page header."""
import html
import re

ARXIV_URL = None
CODE_URL = 'https://github.com/shutongliu-dev/rldexagents-web'

PAPER_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 2h8l5 5v14a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1Zm8 1.8V8h4.2L14 3.8ZM8 11v1.5h8V11H8Zm0 4v1.5h8V15H8Zm0 4v1.5h5V19H8Z"/></svg>'
CODE_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 .8a11.2 11.2 0 0 0-3.54 21.83c.56.1.77-.24.77-.54v-2.08c-3.13.68-3.79-1.33-3.79-1.33-.51-1.3-1.25-1.64-1.25-1.64-1.02-.7.08-.68.08-.68 1.13.08 1.73 1.16 1.73 1.16 1 1.72 2.63 1.22 3.27.93.1-.73.4-1.22.71-1.5-2.5-.28-5.13-1.25-5.13-5.54 0-1.22.44-2.22 1.16-3-.12-.28-.5-1.42.11-2.96 0 0 .94-.3 3.08 1.15a10.7 10.7 0 0 1 5.6 0c2.14-1.45 3.07-1.15 3.07-1.15.61 1.54.23 2.68.11 2.96.73.78 1.16 1.78 1.16 3 0 4.3-2.63 5.25-5.14 5.53.4.35.76 1.04.76 2.1v3.05c0 .3.2.65.78.54A11.2 11.2 0 0 0 12 .8Z"/></svg>'


def add_project_links(page):
    if ARXIV_URL:
        paper = f'<a class="link-pill" href="{html.escape(ARXIV_URL, quote=True)}" target="_blank" rel="noopener">{PAPER_ICON}<span>Paper (arXiv)</span></a>'
    else:
        paper = f'<span class="link-pill" role="link" aria-disabled="true" tabindex="0" title="Paper link coming soon">{PAPER_ICON}<span>Paper (arXiv)</span></span>'
    code = f'<a class="link-pill" href="{CODE_URL}" target="_blank" rel="noopener">{CODE_ICON}<span>Code</span></a>'
    links = f'<nav class="project-links" aria-label="Project resources">{paper}{code}</nav>'
    page = re.sub(r'<nav class="project-links".*?</nav>', '', page, flags=re.S)
    page, count = re.subn(r'(<header class="report-hero">.*?)(<figure>)', lambda m: m[1] + links + m[2], page, count=1, flags=re.S)
    if count != 1:
        raise ValueError('Project-page header not found')
    return re.sub(r'(href="assets/rldex_report\.css)(?:\?[^"\s]*)?"', r'\1?v=project-links-20261027"', page)
