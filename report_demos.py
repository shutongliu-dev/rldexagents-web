"""Reserve an early Demo section for the project's rollout videos."""
from pathlib import Path
import html
import json
import re


def promote_demos(page, root):
    manifest = Path(root) / 'data/rollout_demos.json'
    demos = json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else []
    cards = []
    for demo in demos:
        title = html.escape(demo['title'])
        poster = f' poster="{html.escape(demo["poster"])}"' if demo.get('poster') else ''
        cards.append(
            '<article class="featured-demo">'
            f'<div class="featured-demo-heading"><h3>{title}</h3></div>'
            f'<video controls playsinline preload="none"{poster} aria-label="{title}">'
            f'<source src="{html.escape(demo["video"])}" type="video/mp4">'
            f'<a href="{html.escape(demo["video"])}">Watch video</a></video>'
            + (f'<p class="demo-rollout-caption">{html.escape(demo["caption"])}</p>' if demo.get('caption') else '')
            + '</article>'
        )
    content = ('<div class="featured-demo-grid">' + ''.join(cards) + '</div>') if cards else (
        '<div class="demo-pending"><p>Rollout videos coming soon.</p></div>'
    )
    section = (
        '<section id="demos" class="featured-demos" aria-labelledby="demos-heading">'
        '<div class="featured-demos-heading"><h2 id="demos-heading">Demos</h2>'
        '<span>Rollout demonstrations</span></div>' + content + '</section>'
    )
    if 'class="featured-demos"' in page:
        page, count = re.subn(r'<section id="demos" class="featured-demos"[^>]*>.*?</section>', lambda _: section, page, count=1, flags=re.S)
        if count != 1:
            raise ValueError('Could not update the existing Demo section')
    else:
        target = r'(<h2\b[^>]*id="2-from-hand-motions-to-pose-manifolds"[^>]*>)'
        page, count = re.subn(target, lambda match: section + '\n' + match[1], page, count=1)
        if count != 1:
            raise ValueError('Missing insertion point before section 2')
    if '<a href="#demos">' not in page:
        nav_target = '<li><a href="#2-from-hand-motions-to-pose-manifolds">'
        if nav_target not in page:
            raise ValueError('Missing section 2 navigation item')
        page = page.replace(nav_target, '<li class="toc-demo"><a href="#demos">Demos</a></li>' + nav_target, 1)
    return page
