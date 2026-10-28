# Report production and scientific checks

Completed: 2026-10-27.

## Delivered

- `index.html`: redesigned RLDexAgents research report; DEX-X template layout with cream background, locally bundled Playfair Display / Roboto Mono fonts, hero overview, black section labels, pill links, fixed contents navigation and matching supplementary-page styling.
- `RLDexAgents_Technical_Report.md`: approximately 7,486 whitespace-separated words, Executive Summary, 11 main sections, reproduction appendix and references.
- `RLDexAgents_Technical_Report.tex`: two-column publication-style source generated from the same Markdown. Seven main figure PDFs and eight tables.
- `references.bib`: six verified publication records; PPO explicitly identified as a preprint. Bibliography keys match the report.
- `figures/`: seven main scientific/architecture figures in PNG/SVG/PDF, actual medoid images, local equation SVGs, human/Wuji analysis and original contact-analysis supplements.
- `evidence/`: copied numeric summaries, selected per-episode results, configuration/code evidence and original source locations.
- `pose_hoi_manifold.html`, `manifold.html`, and existing media: preserved interactive supplementary report.

## Scientific review

The main four-interface counts were checked against all five held-out evaluation summaries. The 2,365-task selection result was checked against the expanded comparison JSON. PCA and coverage curves are built directly from the copied E01 results; survival curves use E06 logged risk/survival results. Reported negative outcomes and unmatched historical comparisons remain explicitly distinguished.

Conditional survival uses each model's own successful-lift set. The 209 shared-success comparison applies only to the separate finger/force stability statistics. Reference-end HOLD, first-lift survival and final-window pose success are not pooled. Geometric near-contact is not presented as measured force; medoids are not called proven functional grasp types. The physical camera image is labeled read-only, with `motion_sent=false`; qualitative user feedback is not converted into a success rate.

The report includes 11 experimental entries, but it is not an exhaustive catalog of every historical training run. It prioritizes audited evidence relevant to the three research questions. Source documentation describing intermediate execution states is superseded by completed result files for numeric claims.

## Browser and artifact validation

Headless Chromium checks passed for:

- Desktop 1520×1000 and mobile 390×844; no mobile horizontal overflow.
- Four visible representative replay videos, including successful H.264 decoding and playback.
- Interactive viewer containing all 6,241 points and five representation choices.
- All report images loaded, all internal navigation/citation anchors resolved, no JavaScript exceptions.
- 117 local HTML references across main page and both interactive supplements: no missing files, no references outside this report folder, no external rendering assets.
- Seven LaTeX figure paths exist; bibliography keys and document environment counts agree.

Screenshots: `assets/previews/rldex_desktop.png`, `rldex_mobile.png`, `rldex_manifold.png`.

## Rebuilding

Run from this directory using a Python environment with NumPy, Matplotlib, Pillow and Markdown:

```bash
python build_rldex_report.py
```

The local environment used was `/home/ruoqu/miniconda3/envs/lab51/bin/python`. The builder reads only bundled report data. It regenerates the main HTML, LaTeX and scientific figures, preserving the older interactive supplement. Do not run the older `build_report.py` to rebuild this new main page: that script generates the previous pose-only entry point.

## LaTeX compilation status

No `pdflatex`, `xelatex`, `tectonic` or `latexmk` executable was found in this environment. The LaTeX source and figure paths were checked, but compilation, final page count and float placement remain **unverified**. No PDF is presented as a compiled LaTeX report.

On a machine with a normal TeX installation, run:

```bash
pdflatex -interaction=nonstopmode RLDexAgents_Technical_Report.tex
bibtex RLDexAgents_Technical_Report
pdflatex -interaction=nonstopmode RLDexAgents_Technical_Report.tex
pdflatex -interaction=nonstopmode RLDexAgents_Technical_Report.tex
```

Review overfull boxes and float positions after compilation. The report targets approximately 10–15 main pages, but no page count is claimed before compilation. Full simulator assets and checkpoints are intentionally not part of this report package; all media and data required to view the report are local.

## DEX-X template update

The user requested adoption of the actual local `dexx-code` template after the first research-style layout. `assets/dexx-template.css` is copied from that project; `assets/rldex_report.css` contains only report-specific adaptations. The header and document builder now use its hero, subtitle, venue-style metadata, quick-link, section-label and footer structures. No DEX-X authors, venue claims or experimental results were copied.

`assets/template-fonts.css` references five bundled font files under `assets/fonts/`, downloaded from the Google Fonts stylesheet used by the original template. Rendering needs no external font connection. `assets/template-supplement.css` applies the same identity to both interactive supplementary pages.

After this update, desktop/mobile browser checks, 6,241-point iframe loading, all image loads, citation anchors and H.264 playback passed again. Main screenshots under `assets/previews/rldex_*.png` show the updated template. Report prose and numeric results were unchanged.
