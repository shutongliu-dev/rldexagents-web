"""Promote the six matched demonstration clips into an early project section."""
from pathlib import Path
import html
import json
import re


def promote_demos(page, root):
    if 'class="featured-demos"' in page:
        return page
    demos = json.loads((Path(root) / 'data/cluster_teacher_demos.json').read_text(encoding='utf-8'))
    cards, records = [], []
    for demo in demos:
        media = demo.get('display_media', demo)
        cluster = int(demo['final_cluster'])
        title = html.escape(demo['object'])
        cards.append(
            '<article class="featured-demo">'
            f'<div class="featured-demo-heading"><h3><span>C{cluster}</span>{title}</h3>'
            f'<span class="demo-duration">{media["duration_s"]:.2f} s</span></div>'
            f'<video controls playsinline preload="none" poster="{html.escape(media["poster"])}" '
            f'aria-label="C{cluster} {title} simulation teacher demonstration">'
            f'<source src="{html.escape(media["video"])}" type="video/mp4">'
            f'<a href="{html.escape(media["video"])}">Watch C{cluster} video</a></video></article>'
        )
        records.append(
            '<article><h4>' + f'C{cluster} / {title}' + '</h4>'
            f'<p class="demo-record-key">{html.escape(demo["key"])}</p>'
            f'<p>Original lift: {"yes" if demo["recorded_rollout_lift_success"] else "no"}. '
            f'Original tail stability: {demo["tail_stable_fraction"]:.0%}.</p>'
            f'<a href="{html.escape(demo["trajectory_npz"])}" download>Original trajectory / NPZ</a></article>'
        )
    section = (
        '<section id="demos" class="featured-demos" aria-labelledby="demos-heading">'
        '<div class="featured-demos-heading"><h2 id="demos-heading">Demos</h2>'
        '<span>Simulation / teacher rollouts</span></div>'
        '<p class="demo-lead">See six selected dexterous interactions, from establishing contact to lifting and holding the object.</p>'
        '<div class="featured-demo-grid">' + ''.join(cards) + '</div>'
        '<div class="featured-demo-footer"><p>Teacher-controlled fingers, with reference wrist motion. Selected examples, not an aggregate success rate.</p>'
        '<a href="pose_hoi_manifold.html#demos">Explore the full demo gallery ↗</a></div>'
        '<details class="demo-records"><summary>Recording details and original measurements</summary>'
        '<p>Each color clip is matched by complete reference identity and trimmed to the original display duration. '
        'Outcome statistics and trajectory files below refer to the original audited recording.</p>'
        '<p>Stable tail HOLD requires at least 2 cm object lift and at least two target-contacting fingertips at 0.5 N or above '
        'in at least 95% of the final 30 simulation ticks. This is not the five-second HOLD evaluation or an autonomous agent trial.</p>'
        '<div class="demo-record-grid">' + ''.join(records) + '</div></details></section>'
    )
    page, removed = re.subn(r'<details\b[^>]*class="demo-playback"[^>]*>.*?</details>', '', page, count=1, flags=re.S)
    if removed != 1:
        raise ValueError('Expected the existing six-video demonstration block')
    target = r'(<h2\b[^>]*id="2-from-hand-motions-to-pose-manifolds"[^>]*>)'
    page, inserted = re.subn(target, lambda match: section + '\n' + match[1], page, count=1)
    if inserted != 1:
        raise ValueError('Missing insertion point before section 2')
    nav_target = '<li><a href="#2-from-hand-motions-to-pose-manifolds">'
    if nav_target not in page:
        raise ValueError('Missing section 2 navigation item')
    page = page.replace(nav_target, '<li class="toc-demo"><a href="#demos">Demos</a></li>' + nav_target, 1)
    return page
