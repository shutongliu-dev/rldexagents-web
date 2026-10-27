"""Render the early real-world and simulation rollout showcase."""
from pathlib import Path
import html
import json
import re


def demo_card(demo):
    title = html.escape(demo['title'])
    poster = f' poster="{html.escape(demo["poster"])}"' if demo.get('poster') else ''
    ratio = f' style="aspect-ratio:{int(demo["width"])}/{int(demo["height"])}"' if demo.get('width') and demo.get('height') else ''
    duration = ''
    if demo.get('duration_s'):
        seconds = int(demo['duration_s'])
        duration = f'<span class="demo-duration">{seconds//60}:{seconds%60:02d}</span>'
    return (
        '<article class="featured-demo">'
        f'<div class="featured-demo-heading"><h4>{title}</h4>{duration}</div>'
        f'<video controls playsinline preload="none"{poster}{ratio} aria-label="{title}">'
        f'<source src="{html.escape(demo["video"])}" type="video/mp4">'
        f'<a href="{html.escape(demo["video"])}">Watch video</a></video>'
        + (f'<p class="demo-rollout-caption">{html.escape(demo["caption"])}</p>' if demo.get('caption') else '')
        + '</article>'
    )


def promote_demos(page, root):
    manifest = Path(root) / 'data/rollout_demos.json'
    demos = json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else []
    groups = []
    for key, title, pending in [
        ('real_world', 'Real-world Deployment', 'Real-world deployment videos coming soon.'),
        ('simulation', 'Simulation Rollouts', 'Simulation rollout videos coming soon.'),
    ]:
        entries = [d for d in demos if d.get('group', 'real_world') == key]
        content = ('<div class="featured-demo-grid">' + ''.join(demo_card(d) for d in entries) + '</div>') if entries else (
            '<div class="demo-pending"><p>' + pending + '</p></div>'
        )
        groups.append(f'<div class="demo-group" data-demo-group="{key}"><h3 class="demo-group-title">{title}</h3>{content}</div>')
    section = (
        '<section id="demos" class="featured-demos" aria-labelledby="demos-heading">'
        '<div class="featured-demos-heading"><h2 id="demos-heading">Demos</h2></div>'
        '<p class="demo-editing-note">Videos are edited for brevity, with extended planning and reasoning pauses shortened or omitted.</p>'
        + ''.join(groups) + '</section>'
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
