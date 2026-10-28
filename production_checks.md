# Current report production and checks

## Main narrative

The main report follows motion data → pose structure → executable RL interactions → command-conditioned distillation → agent toolkit. It contains a 148-word abstract, seven numbered sections, four main figures and two core tables. Markdown is approximately 3,700 whitespace-separated words, targeting a 6–8-page main text; final LaTeX page count remains unverified.

The previous detailed text and experimental breakdowns are preserved in `supplementary_report.html`, `RLDexAgents_Supplementary_Report.md`, and `RLDexAgents_Supplementary_Report.tex`. Prior production notes are in `production_checks_extended.md`. Historical metrics and artifacts have not been discarded.

## Main visual structure

- Figure 1 uses the user-provided `method.pdf`. The webpage displays a local SVG conversion; clicking opens the original PDF. PNG and a vector PDF copy support Markdown and LaTeX. The caption distinguishes proposed skill expansion from demonstrated results.
- Figure 2 centers a large HOI manifold in the interactive source palette, with six gesture callouts linked to their actual medoid coordinates. The initial camera/projection matches the interactive viewer.
- Figure 3 explains four command interfaces, shared feedback/control and teacher supervision.
- Figure 4 combines the supported API path with time-separated recorded teacher interaction views. It does not claim an autonomous agent demonstration.

The page retains the DEX-X template, locally bundled fonts and self-contained media. The manifold viewer is **visible by default near the top, before Abstract**, with dataset-source coloring and filters. The recorded demo players remain optional to keep the main reading path concise.

## Source-name audit

All 68 references formerly displayed under a dated HOI export label were matched to the combined human-wrist manifest. Every matching metadata file declares `OakInk-v2` as the source: 27 original wrist-only and 41 expanded references, all right hand. Display labels are now **OakInk (wrist-adapted)**. This is distinguished from the other 672 OakInk references to expose the processing difference. Raw trajectory keys, object identifiers and storage paths are unchanged.

See `data/DATASET_DISPLAY_NAMES.md` and the complete `data/wrist_adapted_source_audit.json` for evidence.

## Verification

- Main HTML: four figure elements, two tables, six playable simulation videos and one source-aware interactive iframe.
- Chromium desktop and mobile checks passed: all images load, navigation anchors resolve, no JavaScript exceptions, H.264 playback succeeds, mobile width remains within 390 px.
- Viewer is before Abstract and expanded; default color is dataset source. Isolating OakInk (wrist-adapted) displays exactly 68 points, restoring all sources displays 6,241.
- Main page links directly to the original method PDF.
- 150 local references across main, extended and interactive pages resolved without external rendering dependencies or paths outside the report.
- Primary matched-interface and expanded-selection numbers still agree with local JSON results. Markdown/LaTeX figure paths and bibliography keys resolve.

## Rebuilding

Run `python build_rldex_report.py` using NumPy, Matplotlib, Pillow and Markdown, with Poppler `pdftoppm` / `pdftocairo` available for the supplied method PDF. It uses only assets and evidence inside this report directory. `build_extended_report.py` targets the extended report; `build_report.py` is the older pose-gallery builder and should not be used to rebuild the main narrative.

No LaTeX compiler is installed in the inspected environment. Source and figure references are checked, but LaTeX compilation, page count and float layout are not certified. On a TeX-equipped machine, use pdflatex → bibtex → pdflatex → pdflatex on `RLDexAgents_Technical_Report.tex`.

Figure 2 update: all six annotation trajectory IDs and medoid indices were checked against the manifold metadata; palette is read from the interactive page itself. PNG/SVG/PDF and the report caption were regenerated, and the final image was visually inspected for overlapping labels.

## Current cluster demo replacement

The user-selected Isaac Sim teacher gallery now supplies the active demos: six videos, 18 snapshots, six trajectory NPZ files, and source manifest copied to `assets/cluster_teacher_rollouts/`. All six keys match their final link-near labels in the existing 6,241-point manifold. Main-page videos, Figure 4, the interactive gallery and its cluster-card HOI snapshots now use these assets. Historical result JSONs and archived old media remain unchanged. New tail-HOLD labels are not merged with earlier pick-and-pose or five-second results.
