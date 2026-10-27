"""Render the open-questions Markdown as a standalone audience-facing page."""
from pathlib import Path
import html
import re
from site_assets import add_site_icons


def build_open_questions_page(root):
    root = Path(root)
    source = (root / 'open_questions.md').read_text(encoding='utf-8')
    lines = source.splitlines()
    cutoff = next((i for i, line in enumerate(lines) if line.strip() == '## Production notes'), len(lines))
    pre = lines[2:cutoff]
    table_start = next((i for i, line in enumerate(pre) if line.startswith('|')), len(pre))
    intro = '<p>' + '</p><p>'.join(html.escape(line.strip()) for line in pre[:table_start] if line.strip()) + '</p>'
    table_lines = [line for line in pre[table_start:] if line.startswith('|')]
    rows = []
    for line in table_lines:
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if cells and not all(re.fullmatch(r'[-: ]+', cell) for cell in cells):
            rows.append(cells)
    table = '<div class="open-questions-table"><table><thead><tr>' + ''.join(f'<th>{html.escape(cell)}</th>' for cell in rows[0]) + '</tr></thead><tbody>'
    table += ''.join('<tr>' + ''.join(f'<td>{html.escape(cell)}</td>' for cell in row) + '</tr>' for row in rows[1:]) + '</tbody></table></div>'
    notes = lines[cutoff + 1:] if cutoff < len(lines) else []
    notes_html = '<h2 class="tagline" id="production-notes">Production notes</h2><p>' + '</p><p>'.join(html.escape(line.strip()) for line in notes if line.strip()) + '</p>' if notes else ''
    body = intro + table + notes_html
    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RLDexAgents — Open Questions</title><meta name="description" content="Open research questions and concrete verification experiments for RLDexAgents."><link rel="stylesheet" href="assets/template-fonts.css"><link rel="stylesheet" href="assets/dexx-template.css"><link rel="stylesheet" href="assets/rldex_report.css?v=open-questions-20261027"><link rel="icon" href="favicon.ico?v=1" sizes="any"><link rel="icon" type="image/png" sizes="32x32" href="assets/favicon-32.png?v=1"><link rel="apple-touch-icon" sizes="180x180" href="assets/favicon-180.png"></head><body><main class="main-content open-questions-page"><header class="report-hero"><h1 class="hero-text">RLDexAgents</h1><div class="sub-hero-text">Open Questions</div><p class="report-subtitle">Proposed verification experiments and evidence boundaries</p><div class="venue">Research agenda · 27 October 2026</div><p><a href="index.html">← Return to the main report</a></p></header><article class="section"><h2 class="tagline" id="open-questions">Open questions</h2>{body}</article></main></body></html>'''
    (root / 'open_questions.html').write_text(add_site_icons(page), encoding='utf-8', newline='\n')
