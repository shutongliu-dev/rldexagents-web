# RLDexAgents experiment index

Evidence audit: 2026-10-27. Paths in this index are relative to this report unless explicitly absolute. Numeric artifacts are copied into `evidence/`; original locations appear in [SOURCE_PATHS.tsv](evidence/SOURCE_PATHS.tsv). Checkpoints remain in their training/output directories; this is a report package, not a model distribution. “Not recorded” means evidence was not verified in this audit.

## E01 — Pose-bank representation and coverage (2026-10-27)

- **Teacher/student/actions:** not applicable; offline Sharpa 22-joint analysis.
- **Data/split:** 1,029,112 indexed poses; 1,015,044 pass URDF limits. Thirteen sources; trajectory-key train/test partition; source caps produce 8,867 fitting and 5,016 test poses.
- **Budget:** K = 6, 12, 24, 48, 96, 192; PCA dimensions 4, 6, 8, 10, 14, 22 for reconstruction. Approximate medoid optimization, candidate pool 4,000, up to eight updates. Single analysis seed.
- **Evaluation:** joint RMS coverage, normalized pairwise bank diversity, fingertip FK reconstruction, leave-one-source-out coverage. Joint-limit violations measured before clipping; FK after clipping.
- **Results:** [summary](evidence/E01_pose_bank/summary.json), [bank metrics](evidence/E01_pose_bank/bank_metrics.csv), [source generalization](evidence/E01_pose_bank/source_generalization.csv).
- **Finding:** K=24 joint KMeans representatives 0.2263 rad macro-median coverage versus random 0.2597 rad. PCA-14 reconstruction 10.11 mm mean fingertip FK error after clipping.
- **Confounders:** source balancing changes the population; temporal correlation; no simulator collision validation. KMeans representatives are nearest observed samples, not raw centroids.

## E02 — Full-HOI geometric contact manifold (2026-10-25–26)

- **Teacher:** success videos use object-goal model_3200; the feature clustering itself does not train a policy.
- **Data:** 6,241 reference records, 3,185 parents; one selected interaction configuration per record. Five representations, K=6, three restarts, parent weighting and block scaling.
- **Inputs:** joints; selected variants add palm/object relations, object shape, fingertip relations, 26-link proximity and normalized distances.
- **Results:** [method comparison](evidence/E02_contact_manifold/summary.json), [assignments](data/final_cluster_assignments.csv), [medoids](data/medoids.json), [interactive projection](manifold.html), [recorded successful demos](data/successful_demos_remapped.json).
- **Finding:** link-near-and-distance restart ARI ≈0.997, silhouette ≈0.087. Final cluster counts 2,278 / 1,560 / 624 / 644 / 374 / 761.
- **Confounders:** geometric proximity is not measured force. Historic pose labels and PhysX-contact labels are distinct partitions. Twelve localized success videos remap to final counts 4 / 2 / 4 / 0 / 0 / 2; no fabricated C3/C4 success examples.

## E03 — Cross-embodiment analysis (2026-10-26)

- **Policy:** none. Wuji2 FK landmarks retargeted independently to Sharpa.
- **Data/budget:** 175 episodes, 95,890 frames; 1,400 sampled poses (eight per episode). Existing human analysis contains 915,392 normalized 60D landmark poses.
- **Results:** [Wuji summary](evidence/E03_wuji/summary.json), [assignments](evidence/E03_wuji/assignments.csv), [human/robot audit](evidence/notes/HAND_METRICS_CROSS_EMBODIMENT_20261026.md).
- **Finding:** mean Wuji→Sharpa fingertip fit error 4.13 mm; human landmark PCA 95% dimension 10, filtered Sharpa all/HOI/freehand 13/14/9.
- **Confounders:** Wuji field ordering needs anatomical confirmation; independent pose fitting, no temporal/contact validation; human and robot dimensions use different feature spaces.

## E04 — Full-HOI object-goal teacher continuation (2026-10-26)

- **Checkpoint:** `/mnt/cpfs/workspace/rq_ws/outputs/full_hoi_wrist_offset_20261026/train_contact_priority/model_5200.pt`; initialized from object-pose posttrain model_3200.
- **Input/actions:** SONIC reference-conditioned teacher; eight-frame state history, six future reference samples; finger position actions and externally supplied wrist motion. Object-only reward does not remove reference observations.
- **Data:** 6,244 HOI records = previous 6,241 + three RoboTool records; 8,192 environment slots, no freehand records in this continuation.
- **Budget:** 3,200→5,200 updates; 32 steps/update; nominal 524,288,000 environment transitions computed from settings, not an independently reconciled counter. LR 5e-5, five epochs, minibatch 1,024.
- **Config/results:** [stage config](evidence/E04_teacher/train_stage.yaml); same-protocol final evaluation in E07. The full-data teacher success rate cannot be inferred from the success-selected E07 pool.
- **Reward:** object position/orientation/fine-pose weights 16/12/8; fine region 3 cm/30 degrees. Final reward window 10. Hand-tracking reward weights zero in this continuation.
- **Confounders:** changing DR and sampling during continuation; no matched scratch control. 378 contact-priority records upweighted, all records retained.

## E05 — Balanced full-data link-near student (2026-10-26)

- **Teacher:** E04 model_5200. **Student:** eight-frame recurrent cluster-conditioned policy, inherited older 28-task weights, new cluster columns reset. 22 normalized joint actions; external wrist.
- **Data:** 2,244 references (374/class), 2,160 parents, 954 assets. Evaluation reuses this training reference pool.
- **Budget:** 300 mixed PPO/teacher-imitation updates, 2,244 environments, 32 steps, three epochs, minibatch 4,096, imitation weight 0.9→0.5; elapsed ≈996 s.
- **Evaluation:** open start; FORM 30 steps, additional HOLD 30, RELEASE 30, nominal geometry. [Summary](evidence/E05_full_student/eval_student_full_20261026/summary.json).
- **Finding:** 362 sustained dual-finger lifts among 1,645 references with ≥2 cm lift target; strict tail-pose success 35/2,244.
- **Confounders:** balanced pose classes do not balance executable grasps; this tail-HOLD test is not five-second HOLD. Qualitative user-reported real execution is not a quantified real-robot experiment.

## E06 — Command ablation, spatial robustness and contact analysis (2026-10-26–27)

- **Teachers:** General model_4999 for 13 tasks, object-goal model_3200 for 15; record-specific assignment in raw rows.
- **Student:** same H=8 recurrent 117D/frame policy; E0 zero command, E1 fixed random grouping, E2 historical pose-cluster grouping; 22 joint actions.
- **Data:** 28 selected DexYCB task references, no held-out parent generalization claim. Not the E02 link-near partition.
- **Budget:** BC 4,200 rows/six epochs; 24 DAgger rounds ×4,200 labels, six epochs per round; FIFO 100k, minibatch 512, AdamW 5e-5, beta decay 0.78, seed 42. Total 105k labels including BC, 15,864 gradient steps.
- **Evaluation:** nominal 28/model; separate spatial run 28 nominal +140 global perturbations +140 object-relative perturbations/model. Lift ≥2 cm plus two fingers ≥0.5 N for 15 frames. HOLD measured from reference end, ≥95% valid frames and no ≥0.2 s drop; see report for separate survival definition.
- **Primary files:** [raw results](evidence/E06_commands/results/), [contact statistics](evidence/E06_commands/contact_analysis/analysis.json), [paired-success stability](evidence/E06_commands/contact_analysis/matched_success_stability.json).
- **Finding:** nominal E0/E1/E2 five-second HOLD 13/17/17 of 28. Global E1/E2 HOLD 92/82 of 140. Paired cluster-minus-random interval includes zero.
- **Confounders:** one training seed; five perturbations/task correlated. Bootstrap unit is task, not rollout. Spatial-run nominal teacher differs by one success from the independent nominal run.

## E07 — Matched four-interface comparison (2026-10-27)

- **Teacher:** E04 model_5200. **Student:** frame MLP 192 → GRU 192 → MLP 128 → tanh 22; Cluster/Joint/Fingertip/Hybrid frame widths 117/133/126/132.
- **Data:** teacher screening of 2,244 candidates yields 340 successful parent trajectories; 272 training and 68 parent-held-out for this student experiment. Earlier pretraining and teacher exposure are not held out.
- **Commands:** actual teacher joint pose at first confirmed lift; fingertip goals are its palm-frame FK, not MANO annotations.
- **Budget:** 300 updates ×32 steps, three epochs, minibatch 4,096; actor LR 3e-6, critic 3e-4; first five updates critic-only; teacher imitation weight 0.9→0.5 over 200 updates. Same previous 28-task backbone, all new command columns zeroed. Effective transitions 1,191,244/interface; optimizer steps 1,619–1,625; elapsed around 13 minutes/interface.
- **Input/actions:** 107D feedback + phase one-hot/age + interface command, eight frames. Privileged training critic. Student executes actions while teacher labels visited states; no teacher/student action blending in this experiment.
- **Evaluation:** nominal geometry, open start, first 30 FORM steps supervised open; teacher tracking in HOLD; extra HOLD 150 steps, RELEASE 30. Lift/HOLD protocol as E06, not E05 tail-pose success.
- **Results:** [all raw summaries and episodes](evidence/E07_interfaces/). Held-out teacher 64/60/54; Cluster 39/27/24; Joint 34/27/26; Fingertip 35/24/22; Hybrid 41/31/25 (lift/1s/5s, denominator 68).
- **Confounders:** success-selected set, heavily imbalanced cluster distribution, one training seed; shared pretrained weights; fixed commands may not identify a complete dynamic teacher trajectory.

## E08 — Latent-prior and seed gesture replacement (2026-10-25)

- **Student/data:** latent prior trained on 1,016 records, 812/204 split; fixed-seed historical student uses a different 663-record multi-round DAgger recipe. Teacher checkpoint and identical training exposure cannot be established from the paired result CSV alone.
- **Budget:** latent 5,000 updates, batch 512. Not matched to seed student.
- **Evaluation:** 141 same-object, different-parent/cluster gesture replacements from the latent held-out pool. [Paired outcomes](evidence/E08_latent/paired_results.csv), [fixed-state sensitivity](evidence/E08_latent/fixed_state_results.csv).
- **Finding:** latent original/swapped lift 31/36; seed 45/33. Latent action change FORM/HOLD 0.017/0.008 rad versus seed 0.118/0.108 rad.
- **Confounders:** architecture, budgets and data all differ; this diagnoses weak command sensitivity but does not establish an architecture ranking.

## E09 — Runtime and agent-facing demonstrations (2026-10-25–27)

- **Implementation:** `../gesture_grasp_tool`, model-specific adapters; old `GraspSkill` API differs from current default link-near controller.
- **Physical record:** [read-only workflow summary](evidence/E09_runtime/summary.json) reports cameras and hand connectivity, `motion_sent=false`, hand not enabled. Separate qualitative feedback reports successful physical grasping without countable trials/video-to-checkpoint linkage.
- **Agent evaluation:** existing [DexBench records](dexbench_results/) distinguish infrastructure errors and safety stops; no confirmed agent end-to-end success. These are not a skill-policy leaderboard.
- **Missing:** calibrated physical HOLD trials, time-synchronized telemetry, agent planning/retry success rates. No quantitative real-robot claim is supported here.

## Source interpretation rules

Counts are not interchangeable: frames, sampled poses, raw trajectories, parent trajectories, segmented references and environment slots describe different units. Reported success counts retain their own denominator and temporal criterion. Historical documentation without local raw records is supporting context only. No score in this index certifies unseen-object or real-world generalization.

## E10 — Manifold-guided demonstration selection, expanded evaluation (2026-10-26)

- **Teacher:** object-goal model_3200. **Students:** historical PhysX contact+joint K6 command; random versus manifold-guided demonstration selection, same v2 learner.
- **Data/budget:** 30 demonstrations, 60,000 teacher queries, 400 updates per student. Exclude both training sets' 40 parents /52 related records from 2,417 candidates; evaluate 2,365 references /1,721 parents. Same objects can occur in training and evaluation.
- **Criterion:** lift ≥2 cm with dual-finger contact for 0.5 s; last 30 steps ≥80% lift retention and ≥50% dual contact. Strict joint pose criterion adds ≥80% frames within 3 cm/30 degrees. This is not E07 five-second HOLD.
- **Primary evidence:** [expanded comparison](evidence/E10_selection/expanded_comparison.json); local per-episode results in `evidence/E10_selection/expanded_eval_v1/`.
- **Finding:** teacher 560/2,365; random 354; guided 343. Guided−random −0.47 pp, paired-parent 5,000-resample 95% interval [−2.13,+1.19] pp. Strict lift+pose 89/32/14.
- **Confounders:** one training seed; historical taxonomy used full-data features; open-hand starts alter some in-hand tasks; RELEASE supplied by runtime. Not unseen-object generalization. Small 14-task guided advantage does not persist at scale.

## E11 — Student-only object-reward PPO continuation (2026-10-26)

- **Initialization:** historical 28-task C0–C5 student; no online teacher labels in this continuation.
- **Input/actions:** H8×117 local feedback plus cluster/phase, 22 normalized position actions; external wrist. RELEASE implemented by runtime.
- **Data/budget:** 28 DexYCB references + three RoboTool references; 496 environments, 400 PPO updates, approximately 19 min 09 s. Real-hand limits, five-second terminal HOLD, ±2 cm translation and ±10 degrees yaw.
- **Evaluation:** original 28 references, one rollout per condition. Short success requires five consecutive HOLD frames with ≥2 cm lift and two valid fingers ≥1 N; five-second full retention is stricter. Tool success instead uses pose <3 cm/30 degrees plus dual contact.
- **Primary records:** [model notes](evidence/E11_student_rl/README.md), four `*_results.json` files alongside them.
- **Finding:** nominal full five-second HOLD 5→8 of 28; perturbed 7→7. Short success 21→21 in both conditions; three tool tasks remain 0/3 in tail retention.
- **Limitations:** different success thresholds from E06/E07, selected training tasks, one rollout, no quantified real-robot test. No demonstrated broad new-tool improvement.

## E12 — Current six-cluster illustrative teacher rollouts

User-selected source: `audit/link_near_cluster_distill_20261026/teacher_rollouts_isaacsim_20261027/index.html`. General teacher 5200, Isaac Sim closed-loop execution with reference wrist and teacher-controlled fingers. One selected reference per current C0–C5; no aggregate generalization claim. All six recorded lift and stable-tail flags are true. Tail success requires height ≥2 cm and two target-contacting fingertips ≥0.5 N in ≥95% of the final 30 simulation ticks. Peak force and >20 N fractions remain visible; success is not a statement that force never exceeds 20 N.

Local assets: `assets/cluster_teacher_rollouts/`; enriched lookup and exact manifold mapping: `data/cluster_teacher_demos.json`. These replace active report videos and Figure 4, not the historical outcomes of E02/E07.
