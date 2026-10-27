"""Build the offline interactive replacement for main-report Figure 2."""
from pathlib import Path
import html
import json
import re
from site_assets import add_site_icons


def build_viewer(root):
    root = Path(root)
    data = json.loads((root / 'data/manifold.json').read_text(encoding='utf-8'))
    annotations = json.loads((root / 'data/figure2_medoid_annotations.json').read_text(encoding='utf-8'))
    method = data['methods']['link_near_and_distance_joint']
    sources = data['datasets']
    medoids = []
    for c in range(6):
        index = int(method['medoids'][str(c)])
        sample = data['metadata'][index]
        medoids.append({'index': index, 'key': sample[0], 'dataset': sample[1], 'frame': sample[4]})
    payload = {
        'coords': method['coords'], 'labels': method['labels'], 'datasets': sources,
        'colors': [annotations['source_palette'][source] for source in sources],
        'sourceIds': [sources.index(sample[1]) for sample in data['metadata']], 'medoids': medoids,
    }
    positions = [(25, 80), (80, 20), (89, 52), (10, 52), (79, 80), (24, 20)]
    cards = ''.join(
        f'<button class="pose" style="left:{x}%;top:{y}%" aria-label="Show C{c} representative" aria-pressed="false">'
        f'<img draggable="false" src="assets/poses/link_near_and_distance_joint/cluster_{c}.png" alt="">'
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
        '<p class="subtitle">6,241 configurations / colors indicate dataset sources / link-near + distance</p></div>'
        '<div class="tools"><button data-zoom-out aria-label="Zoom out">−</button>'
        '<button data-zoom-in aria-label="Zoom in">+</button><button data-reset>Reset view</button></div></header>'
        '<div class="stage"><canvas tabindex="0" aria-label="Interactive 3D hand-object point cloud. Drag to rotate, scroll to zoom, or use the arrow keys."></canvas>'
        + cards + '<div class="tooltip" role="tooltip"></div></div>'
        '<div class="legend" aria-label="Dataset source filters">' + legend + '</div>'
        '<p class="hint">Drag to rotate / scroll to zoom / select a hand to inspect its medoid / toggle sources below the plot</p>'
        '<div class="selection" aria-live="polite">Each hand is linked to its observed medoid. Geometric groups are not validated functional grasp categories.</div>'
        '<script id="pointData" type="application/json">'
        + json.dumps(payload, separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/')
        + '</script><script src="assets/representative-manifold.js"></script></body></html>'
    )
    (root / 'representative_manifold.html').write_text(add_site_icons(page), encoding='utf-8', newline='\n')


def embed_viewer(page):
    def replace(match):
        return (
            '<figure class="representative-manifold-figure">'
            '<iframe class="representative-manifold" src="representative_manifold.html" '
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
