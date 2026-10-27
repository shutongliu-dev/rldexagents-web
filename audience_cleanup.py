"""Keep internal production/provenance material out of the audience-facing page."""
import re

CAPTIONS = {
    1: 'Figure 1 — Toolkit overview: motion organization, teacher-to-student distillation, agent interfaces, and a proposed skill-expansion loop.',
    2: 'Figure 2 — Hand–object manifold and representative configurations C0–C5. Colors indicate dataset sources; each hand is linked to its observed medoid. These groups describe geometry rather than validated grasp functions.',
    3: 'Figure 3 — Four command interfaces share hand-local feedback, a recurrent architecture, and the same action space. A privileged teacher labels states visited by the student.',
    4: 'Figure 4 — Toolkit execution and six selected Isaac Sim teacher interactions, one per cluster. Finger control is closed-loop; wrist motion follows the reference.',
}


def refresh_assets(page):
    return re.sub(
        r'((?:href|src)="assets/(?:report\.js|template-supplement\.css|rldex_report\.css|representative-manifold\.(?:css|js)))(?:\?[^"\s]*)?"',
        r'\1?v=audience-20261027"', page,
    )


def hide_internal(tag):
    if 'data-maintenance' not in tag:
        tag = tag[:-1] + ' data-maintenance hidden>'
    return tag


def clean_main(page):
    page = re.sub(r'<div class="authors"[^>]*>', lambda m: hide_internal(m[0]), page)
    page = re.sub(r'<footer class="footer"[^>]*>', lambda m: hide_internal(m[0]), page)
    for match in list(re.finditer(r'<figcaption[^>]*>(Figure ([1-4])\s*[—–-].*?)</figcaption>', page, re.S)):
        # Update matching image alt text too; keep the original report sources intact.
        page = page.replace(match[1], CAPTIONS[int(match[2])])

    def explorer(match):
        block = match[0]
        block = re.sub(r'<p>.*?</p>', '<p>Drag to rotate the point cloud, scroll to zoom, and use source filters to explore the hand-pose distribution.</p>', block, count=1, flags=re.S)
        block = re.sub(r'\s*·\s*<a href="data/wrist_adapted_source_audit.json">Source audit</a>', '<a href="data/wrist_adapted_source_audit.json" data-maintenance hidden>Source audit</a>', block)
        return block
    page = re.sub(r'<section class="interactive-evidence" id="interactive-manifold">.*?</section>', explorer, page, flags=re.S)

    def demo(match):
        block = match[0]
        block = re.sub(r'<p>', '<p data-maintenance hidden>', block)
        block = re.sub(r'<a href="[^"]+" download>', lambda m: hide_internal(m[0]), block)
        return block
    page = re.sub(r'<div class="cluster-rollout">.*?</div>', demo, page, flags=re.S)
    page = page.replace('Cluster demonstrations · six Isaac Sim teacher rollouts', 'Teacher demonstrations')
    page = re.sub(r'<p>Current C0–C5, one selected rollout each\..*?</p>', '<p>Six selected teacher interactions, one per configuration family. The teacher controls the fingers while the wrist follows its reference.</p>', page, flags=re.S)
    page = page.replace('Snapshots, forces and manifold locations', 'Explore the demonstrations')
    page = page.replace('These materials preserve the detailed evidence without interrupting the main narrative.', '')
    return refresh_assets(page)


def clean_manifold(page):
    page = re.sub(r'(<header><h1>.*?</h1>)<p>.*?</p>', r'\1<p>Explore 6,241 hand–object configurations. Drag to rotate, scroll to zoom, and select points or cluster representatives.</p>', page, count=1, flags=re.S)
    page = page.replace('Projection diagnostics', 'Projection statistics')
    page = re.sub(r'<div class="axisnote">.*?</div>', '<div class="axisnote">Each representation uses its own PCA projection.</div>', page, count=1, flags=re.S)
    return refresh_assets(page)


def clean_gallery(page):
    return refresh_assets(re.sub(r'<footer[^>]*>', lambda m: hide_internal(m[0]), page))
