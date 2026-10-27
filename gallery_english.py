"""Apply the English gallery copy without rewriting embedded experiment data."""
from pathlib import Path
from site_assets import add_site_icons
import json
import re


def localize_gallery(path):
    path = Path(path)
    translations = json.loads((path.parent / 'data/gallery_english_strings.json').read_text(encoding='utf-8'))
    page = path.read_text(encoding='utf-8')
    parts = re.split(r'(<script\b[^>]*>.*?</script>)', page, flags=re.S)
    for i in range(0, len(parts), 2):
        for source, english in sorted(translations.items(), key=lambda item: -len(item[0])):
            parts[i] = parts[i].replace(source, english)
    page = ''.join(parts)
    page = page.replace('lang="zh-CN"', 'lang="en"')
    page = re.sub(r'<title>.*?</title>', '<title>Hand Pose &amp; HOI Manifolds — Research Supplement</title>', page, count=1)
    page = re.sub(r'<div class="eyebrow">.*?</div>', '<div class="eyebrow">RLDexAgents / Research Supplement / 27 October 2026</div>', page, count=1)
    page = re.sub(r'<h1>.*?</h1>', '<h1>Hand Pose &amp;<br><em>HOI Manifolds</em></h1>', page, count=1, flags=re.S)
    if 'class="gallery-page"' not in page:
        page = page.replace('<body>', '<body class="gallery-page">', 1)
    for sheet in ['assets/template-supplement.css', 'assets/gallery.css']:
        if f'href="{sheet}"' not in page:
            page = page.replace('</head>', f'<link rel="stylesheet" href="{sheet}"></head>', 1)
    page = page.replace('placeholder="banana / mug / marker…"', 'placeholder="Search trajectory or object"')
    path.write_text(add_site_icons(page), encoding='utf-8', newline='\n')


if __name__ == '__main__':
    localize_gallery(Path(__file__).parent / 'pose_hoi_manifold.html')
