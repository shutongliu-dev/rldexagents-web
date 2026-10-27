"""Build the offline interactive replacement for main-report Figure 2."""
from pathlib import Path
import html
import json
import re
from PIL import Image
from site_assets import add_site_icons
from audience_cleanup import refresh_assets


def build_viewer(root):
    root = Path(root)
    data = json.loads((root / 'data/manifold.json').read_text(encoding='utf-8'))
    annotations = json.loads((root / 'data/figure2_medoid_annotations.json').read_text(encoding='utf-8'))
    method = data['methods']['link_near_and_distance_joint']
    sources = data['datasets']
    medoids = []
    pose_dir = root / 'assets/representative-poses'
    pose_dir.mkdir(exist_ok=True)
    for c in range(6):
        index = int(method['medoids'][str(c)])
        sample = data['metadata'][index]
        medoids.append({'index': index, 'key': sample[0], 'dataset': sample[1], 'frame': sample[4]})
        image = Image.open(root / f'assets/poses/link_near_and_distance_joint/cluster_{c}.png').convert('RGB')
        bbox = image.convert('L').point(lambda value: 255 if value < 235 else 0).getbbox()
        if bbox:
            x0, y0, x1, y1 = bbox
            image = image.crop((max(0, x0-14), max(0, y0-14), min(image.width, x1+14), min(image.height, y1+14)))
        image.thumbnail((320, 320), Image.Resampling.LANCZOS)
        image.save(pose_dir / f'cluster_{c}.png')
    payload = {
        'coords': method['coords'], 'labels': method['labels'], 'datasets': sources,
        'colors': [annotations['source_palette'][source] for source in sources],
        'sourceIds': [sources.index(sample[1]) for sample in data['metadata']], 'medoids': medoids,
    }
    positions = [(25, 80), (80, 20), (89, 52), (10, 52), (79, 80), (24, 20)]
    cards = ''.join(
        f'<button class="pose" style="left:{x}%;top:{y}%" aria-label="Show C{c} representative" aria-pressed="false" '
        'aria-description="Drag to reposition. Arrow keys move the hand; Home restores its position.">'
        f'<img draggable="false" src="assets/representative-poses/cluster_{c}.png" alt="">'
        f'<strong>C{c}</strong></button>' for c, (x, y) in enumerate(positions)
    )
    legend = ''.join(
        f'<button data-source="{i}" aria-pressed="true" style="--source:{payload["colors"][i]}">'
        f'<i aria-hidden="true"></i>{html.escape(source)}</button>' for i, source in enumerate(sources)
    )
    page = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Interactive hand-object representatives</title>'
        '<link rel="stylesheet" href="assets/representative-manifold.css"></head><body>'
        '<header><div><h1>Hand-object manifold &amp; representative configurations</h1>'
        '<p class="subtitle">6,241 hand–object configurations</p></div>'
        '<div class="tools" role="group" aria-label="Point cloud controls">'
        '<button data-mode="rotate" aria-pressed="true">Rotate</button>'
        '<button data-mode="move" aria-pressed="false">Move</button>'
        '<button data-zoom-out aria-label="Zoom out">−</button>'
        '<button data-zoom-in aria-label="Zoom in">+</button><button data-reset>Reset view</button></div></header>'
        '<div class="stage"><canvas tabindex="0" aria-label="Interactive 3D hand-object point cloud. Drag to rotate; select Move or hold Shift and drag to reposition. Scroll to zoom. Arrow keys rotate; Shift plus arrow keys move."></canvas>'
        + cards + '<div class="tooltip" role="tooltip"></div></div>'
        '<div class="legend" aria-label="Dataset source filters">' + legend + '</div>'
        '<p class="hint">Drag cloud to rotate · Shift + drag to move cloud · Drag hands to rearrange · Scroll to zoom</p>'
        '<div class="selection" aria-live="polite"></div>'
        '<script id="pointData" type="application/json">'
        + json.dumps(payload, separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/')
        + '</script><script src="assets/representative-manifold.js"></script></body></html>'
    )
    page = add_site_icons(refresh_assets(page))
    page = re.sub(r'(assets/representative-manifold\.(?:css|js))\?[^"\s]*', r'\1?v=hands-20261027', page)
    (root / 'representative_manifold.html').write_text(page, encoding='utf-8', newline='\n')


def embed_viewer(page):
    def replace(match):
        return (
            '<figure class="representative-manifold-figure">'
            '<iframe class="representative-manifold" src="representative_manifold.html?v=hands-20261027" '
            'title="Rotate the 3D hand-object manifold and inspect six representative hand configurations" loading="lazy"></iframe>'
            '<noscript><img src="figures/main02_manifold.svg" alt="Static hand-object manifold and six representative hand configurations"></noscript>'
            + match.group(1) + '</figure>'
        )
    return re.sub(r'<figure><img[^>]+src="figures/main02_manifold.svg"[^>]*>(<figcaption.*?</figcaption>)</figure>', replace, page, flags=re.S)


if __name__ == '__main__':
    root = Path(__file__).parent
    build_viewer(root)
    page = root / 'index.html'
    page.write_text(embed_viewer(page.read_text(encoding='utf-8')), encoding='utf-8', newline='\n')
