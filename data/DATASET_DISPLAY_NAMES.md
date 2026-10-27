# Manifold dataset display names

The 68-record collection previously displayed with a dated export name is now **OakInk (wrist-adapted)**.

Verification matched all 68 manifold trajectory keys to the combined human-wrist reference manifest, then read each matching reference's `metadata.json`. All 68 `config.dataset_root` values identify the local `OakInk-v2` collection, and all 68 are right-hand references. There are 27 `human_wrist_only` and 41 `human_wrist_expansion` entries.

The workflow preserves the source finger motion and rebuilds the pre-contact wrist approach; subsequent retargeting prepares Sharpa references. This collection is not an independent original dataset named after its export date, and its storage inside `robotool_batch` does not establish RoboTool acquisition provenance.

The other 672 entries displayed as OakInk retain their existing name. Keeping the 68 adapted references separate exposes the processing difference rather than silently combining their distributions. Trajectory IDs, object IDs and source paths remain unchanged for lookup.

Evidence: `wrist_adapted_source_audit.json`, including all 68 source metadata paths and matched sequence IDs. The source manifest is `/home/ruoqu/crq_ws/env_dex_bench/env_pick_bench/results/hoi_engine/full_data_rl/full_training/human_wrist_expansion/combined_references.json`.
