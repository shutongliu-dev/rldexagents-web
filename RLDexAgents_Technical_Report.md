# RLDexAgents: An Extensible Dexterous Skill Toolkit for LLM Agents

*From Hand Pose Manifolds to Interface-Conditioned Skill Distillation and Agentic Manipulation*

Technical report · Sharpa right-hand implementation · 27 October 2026

## Abstract

Dexterous robots must turn plausible hand poses into stable physical interactions, while language agents need skills they can invoke without generating joint trajectories. RLDexAgents connects diverse human and robot hand motions to structured pose representations, reinforcement-learning teachers, command-conditioned students, and an extensible skill toolkit. We analyze approximately 915K human poses, 1.03M Sharpa poses, and 1,400 Wuji2 samples. Representative pose banks improve geometric coverage, but pose similarity does not establish equivalent manipulation. Physical teacher rollouts supply executable demonstrations for four interfaces: Cluster, Joint, Fingertip, and Hybrid. On 68 student-held-out tasks, students achieve 50–60% grasp success versus 94% for the teacher; richer commands do not consistently improve retention or target adherence. The toolkit separates high-level skill selection, external wrist control, and 30 Hz tactile hand control. These results establish a working research pipeline while identifying command ambiguity, contact establishment, and teacher–student observation differences as central obstacles to reusable dexterous skills.

## 1. Introduction

A human can demonstrate a grasp with a single hand pose, while a dexterous robot must turn that pose into a physically stable interaction. For an LLM agent, the challenge is greater: it must select a grasp, invoke a suitable controller, and adapt to uncertain contact without directly generating high-dimensional joint trajectories. A hand that looks correctly posed may still miss the object, contact an unsuitable surface, or lose its grip during lifting.

Existing resources offer two complementary starting points. Large human–object interaction (HOI) datasets contain diverse motions, but their trajectories are not organized into a compact vocabulary an agent can readily call. Reinforcement learning (RL) can learn physically effective behavior, but the resulting policies often depend on a particular reference, object or initialization. Static pose libraries lack feedback, while direct full-trajectory imitation exposes more detail than a high-level agent should need to specify.

We ask: **can we organize hand motions into a structured skill space and turn representative behaviors into reusable tools for robotic agents?** RLDexAgents follows one progression: diverse hand motions reveal structured pose variation; representative configurations become skill candidates; RL establishes physically executable interactions; distillation exposes these behaviors through compact commands; an execution toolkit connects those commands to an agent.

![Figure 1 — RLDexAgents method overview: (a) organize human and robot motion into pose families; (b) distill successful RL interactions into command-conditioned students; (c) expose controllers through an agent-facing skill registry; (d) extend the bank with new gestures and skills. Panel (d) describes a proposed expansion loop; the simulation and robot panels illustrate the intended execution settings, not measured end-to-end success rates.](figures/method_overview.png)

Three insights guide this progression. **Representation:** hand poses exhibit structured variation, but geometric similarity does not imply manipulation equivalence. **Learning:** successful RL interaction bridges the gap between plausible poses and executable behaviors. **Interface:** skills can be exposed at different abstraction levels, but more expressive commands are not necessarily easier to distill or control.

The contributions are correspondingly focused:

- **Hand pose organization:** a cross-source analysis and representative pose bank for human and robotic motion, with geometric coverage and interaction-aware clustering.
- **Interface-conditioned distillation:** a common teacher-to-student pipeline and a matched comparison of Cluster, Joint, Fingertip and Hybrid commands.
- **An agentic skill toolkit:** retrieval, command compilation and closed-loop hand-policy execution, with explicit separation of hand control, wrist motion and task verification.

Hand-synergy research motivates studying coordinated posture variation [@santello1998]. DAgger motivates learning from states the student actually visits [@ross2011], while asymmetric learning permits privileged training information [@pinto2018]. Language-grounded skill selection motivates delegating execution to controllers rather than producing low-level actions directly [@ichter2023]. Our experiments connect these ideas within an existing Isaac Lab and Sharpa pipeline. They establish neither universal grasping nor autonomous acquisition of new skills at test time.

## 2. From Hand Motions to Pose Manifolds

### 2.1 A diverse motion collection

The analysis brings together approximately **915K human landmark poses**, **1.03M Sharpa joint poses**, and **1,400 sampled Wuji Hand 2 poses**. Human HOI spans objects and contact-rich activities from sources including DexYCB, HOT3D, OakInk and HRDexDB. Sharpa data combines retargeted interactions, DexCanvas and DexterHand motions, and SharpaDex freehand movement. Wuji2 provides a separate embodiment for a preliminary kinematic comparison.

This diversity is useful but difficult to consume directly. Sources differ in hand representation, sampling density, object geometry and task intent. Freehand data explores configurations without requiring object support; HOI places the hand in object-dependent relationships. Dense sampling from a large source can dominate a naive average or clustering result. We therefore preserve source and parent-trajectory identity and use source-balanced fitting for the quantitative pose-bank analysis. Detailed collection versions and retargeting counts are deferred to the supplementary inventory.

Human analysis uses normalized hand-local landmarks, whereas Sharpa analysis uses 22 ordered joint angles. Wuji2 landmarks are obtained by forward kinematics (FK) and fitted to Sharpa for a cross-hand probe. These are different feature spaces, not interchangeable measures of capability. Joint-limit checking and FK quantify geometric validity; neither alone guarantees collision-free or stable interaction.

### 2.2 Structure of the hand pose space

Principal component analysis (PCA) measures coordinated variation in a chosen representation. For a joint pose, projection and reconstruction are:

$$z=U_k^T(q-\mu),\qquad \hat q=\mu+U_kz.$$

The data exhibit substantial statistical structure: many joint or landmark coordinates vary together, and different sources occupy different parts of the distribution. Sharpa freehand and HOI cohorts have different variance profiles, consistent with their different constraints. This supports organizing motions into posture families rather than treating every frame as an unrelated example.

![Figure 2 — Hand–object manifold and representative hand configurations. The large point view uses the same source colors and initial 3D projection as the interactive viewer. Each C0–C5 hand image is connected to its actual medoid sample; colors identify dataset sources, not pose clusters. The six geometric groups are candidate configuration families, not established functional grasp types.](figures/main02_manifold.png)

A 95% explained-variance threshold summarizes linear compression, not intrinsic manifold dimension. Human landmark dimensions should not be compared directly with robot joint dimensions as an absolute dexterity score. Likewise, retaining variance does not establish sufficient control precision: millimeter-level fingertip deviations may matter when contacts are small. We pair the variance analysis with reconstruction and coverage measurements rather than interpreting a low component count as a complete hand model.

### 2.3 From pose clusters to skill candidates

Clustering provides a compact vocabulary of configurations. Our interaction-oriented representation combines joint posture with hand–object geometry, including which hand links are near the object and their distances. It organizes 6,241 selected HOI configurations into six groups, C0–C5. These labels belong to this representation; they are not anatomical or functional names shared by all historical partitions.

Representatives are observed configurations rather than synthetic average poses. A **pose bank** stores these configurations and their provenance; a **skill candidate** additionally associates a pose with an interaction and possible command. Joint-space KMeans and PCA-based selection improve nearest-entry coverage relative to random selection at a fixed bank size. Medoid selection also provides real examples suitable for retrieval, although it does not consistently outperform other optimized banks in the measured coverage metric.

The central limitation is equally important: **pose clusters provide a compact vocabulary of hand configurations, but their geometric organization alone does not determine functional grasp categories.** Similar joints can produce different contact patterns on different objects. Near-contact geometry is not measured contact force, and an object-local frame does not automatically align semantic axes across assets. Candidate poses must therefore pass through physical execution before being treated as demonstrations of a skill. This motivates RL as the bridge from representation to interaction.

## 3. Learning Executable Dexterous Skills

The learning pipeline turns human and robot HOI references into retargeted robot motions, trains a reference-conditioned RL teacher, and collects successful physical interactions. The teacher is rewarded through simulation, where contact, object motion and stability determine what actually happens. Reference joint positions are not assumed to be the motor targets that would produce the same motion under load.

We reuse the project's PPO-based training framework [@schulman2017]. The teacher observes hand state, object state and reference information, including future motion, and learns finger control while wrist motion is supplied externally. Large parallel simulation supports diverse objects, reference trajectories and randomized physical conditions. The audited general continuation uses roughly 6.2K HOI references and 8,192 environment instances. Those instances are parallel training slots, not additional unique demonstrations.

Goal-oriented post-training emphasizes object-task outcomes, including finer pose accuracy near the desired object pose. This adaptation changes the reward emphasis while preserving the teacher's reference input. It should not be confused with giving the teacher only a compact agent command. Spatial and physical randomization broaden the training conditions, but their presence is not by itself evidence of deployment robustness.

The next step is **successful-rollout filtering**. A physically valid reference is a candidate; an executed trajectory with verified object lift and contact retention is a demonstration. For grasp distillation, we select teacher rollouts that establish sustained multi-finger contact, lift the object and maintain it after the reference ends. This produces a more task-aligned starting point than indiscriminately mixing references that may describe acquisition, supported interaction or pre-grasped manipulation. Our current evidence motivates this choice but does not isolate success filtering as a causal improvement under every matched training setting.

A crucial distinction follows: **a successful reference-tracking policy is not necessarily a reusable grasp controller.** An in-hand reference can start with the object already supported; opening the hand and approaching from a table changes the task. The teacher may also rely on privileged object state or future references unavailable during deployment. Its success establishes executable behavior under the evaluated conditions, not a ready-made high-level interface. Distillation must compress both the behavior and its conditioning into something an agent can specify and a deployed controller can observe.

## 4. Interface-Conditioned Skill Distillation

### 4.1 A common closed-loop student

The student maps recent hand feedback and an active command to finger actions:

$$a_t=\pi_\theta(H_t,c_t).$$

The shared feedback history contains eight 107D frames: joint positions and velocities, previous actions, palm-frame velocities, fingertip force vectors in local and palm frames, and force-validity indicators. It excludes object truth, absolute wrist pose and future references. Wrist motion remains external. At 30 Hz, the student produces 22 normalized actions, decoded into bounded joint-position targets by the runtime. These actions are distinct from measured joint positions and do not directly command contact force.

This separates the feedback loop from the choice of command abstraction. The same kind of local tactile and proprioceptive feedback can support several interfaces, while the agent expresses different amounts of intent.

### 4.2 Four command abstractions

**Cluster** uses a C0–C5 identifier to select a family of configurations. It is compact and easy to retrieve, but leaves the precise hand shape underdetermined. **Joint** supplies a 22D target hand pose, retaining detailed posture while omitting how the object should be contacted. **Fingertip** supplies five palm-frame 3D targets, emphasizing endpoint geometry while leaving internal joint arrangements implicit. **Hybrid** combines the cluster identifier and fingertip targets, providing both a categorical prior and geometric detail.

![Figure 3 — Interface-conditioned distillation. Four command abstractions share hand-local feedback, a recurrent student backbone and the same finger-action interface. The privileged teacher labels student-visited simulator states while retaining its own reference observations. Commands condition the policy; they do not directly overwrite its joint actions.](figures/main03_distillation.png)

Every interface also carries execution phase and phase age. A pose command is a conditioning target, not an immutable joint trajectory. It must leave the controller freedom to accommodate contact. Conversely, a hand-local goal does not specify object location or a safe EEF approach; the external controller remains responsible for bringing the hand into a compatible interaction.

In the matched comparison, all continuous commands derive from the same successful teacher configuration: Joint uses its measured joint pose and Fingertip uses FK of that pose in the palm frame. Hybrid combines those fingertip targets with its cluster label. This avoids comparing incompatible targets across interfaces. It also defines the scope of the result: commands are reference-derived, not independently invented by an agent.

### 4.3 Learning from teacher behavior and student experience

Behavior cloning provides an initial policy from successful behavior. Online DAgger supplies teacher action labels at states reached by the student, while mixed PPO can also optimize physical task outcomes. These mechanisms address different problems: supervised fitting transfers behavior, online labeling exposes execution errors, and policy gradients can improve interaction beyond a static action dataset.

The matched four-interface experiment uses a common pretrained backbone, resets the new command-input weights, and trains each student with the same teacher, success-selected pool and approximately matched mixed imitation/PPO budget. The teacher retains its original observations when labeling student-visited states; the student's compact command does not replace the teacher's reference stream. Training can use privileged critic information while the actor remains limited to its deployable feedback.

More expressive commands therefore face a harder issue than input dimensionality alone. A fixed hand pose may not identify the dynamic action that a reference-tracking teacher should take next. Two nearly identical feedback histories may conceal different object states or impending wrist motions. The student can receive ambiguous supervision even when every teacher rollout is physically successful. The results below show the practical consequence: **more expressive commands do not necessarily yield more successful or more controllable skills under the same distillation procedure.**

## 5. An Extensible Toolkit for LLM Agents

Given an object and a grasp instruction, the intended agent workflow is to retrieve a compatible skill, choose a supported command interface, and delegate 30 Hz finger control to its student policy. The agent handles low-rate intent and tool selection; the hand controller handles local feedback. This is the point at which pose organization, physical learning and interface design come together.

The implemented toolkit supports pose/skill retrieval, command compilation, checkpoint loading, observation preprocessing and status feedback. Registry metadata associates a controller with its command type, hand configuration and runtime requirements. The compiler transforms physical command units into the normalization expected by that policy. The execution host maintains history, supplies tactile measurements, applies action decoding and limits, and coordinates with the external wrist controller.

A supported command sequence is:

```python
tool.call("cluster_grasp", {"cluster": 2, "phase": "FORM"})
target_q_rad = tool.tick(sample)  # host-supplied hand feedback
status = tool.call("get_grasp_status")
```

The host must use the phase semantics associated with the checkpoint. In particular, the current experiments do not all use the same contact-triggered transition rules. The compact API removes the need for the agent to generate 22 joint actions each tick; it does not remove the need to choose an appropriate approach or verify the outcome.

![Figure 4 — Toolkit execution path and six recorded interaction examples. Top: a supported skill call delegates hand feedback and control to the runtime. Bottom: actual Isaac Sim teacher lift snapshots, one for each final link-near cluster C0–C5. These selected closed-loop interactions establish physical demonstrations; they are not autonomous LLM planning trials or a student success-rate comparison.](figures/main04_demonstrations.png)

The local gallery contains representative poses and recorded successful Isaac Sim teacher interactions for all six final clusters. These examples show what the data and controllers can physically support, while retaining the distinction between a pose sample and an executed behavior. They do not establish all six clusters as equally reliable skills. Physical integration also exists, with qualitative positive user feedback, but the audited record lacks repeated, checkpoint-linked real-robot trials from which to calculate a success rate.

Likewise, no formal end-to-end agent success rate is reported here. A valid command and a returned joint target do not certify that an object was grasped. Hand force alone cannot distinguish the intended object from another contact. The runtime exposes feedback, while object-level outcome verification belongs to the surrounding system. Automatic acquisition of a missing skill, learned interface selection and verified grasp-to-in-hand composition remain extensions rather than completed toolkit capabilities.

## 6. Experiments and Key Findings

We focus on three questions: whether pose organization improves coverage, whether command conditioning improves stable execution, and how command expressivity affects distillation. Detailed protocols, historical experiments and per-source breakdowns are retained in the [supplementary report](supplementary_report.html) and [experiment log](experiment_index.md).

### Result A: structured banks improve geometric coverage

A 24-entry representative bank reduces source-macro median nearest-pose error from approximately 0.260 rad for random selection to 0.226 rad for joint-space clustering. This supports the value of organization at a fixed retrieval budget. It does not establish that dimensionality reduction is necessary: joint-space and PCA-based banks perform similarly.

| Analysis | Representation / measure | Key result |
|---|---|---|
| Human posture | Normalized landmarks; 95% PCA variance | 10 components |
| Sharpa posture | Limit-valid joints; all / HOI / freehand | 13 / 14 / 9 components |
| Pose-bank coverage | K=24 joint representatives | 0.226 rad |
| Random-bank coverage | K=24; same source-balanced metric | 0.260 rad |
| Reconstruction precision | PCA-14; mean fingertip FK error after clipping | 10.1 mm |

*Table 1. Core representation results. PCA component counts depend on feature space and population; they are not intrinsic dimensions or cross-hand capability scores. Coverage is source-macro median nearest-entry joint RMS, measured on a trajectory-key split.*

The complementary negative finding is that improved geometric organization does not automatically improve skill selection. Expanded evaluation of a manifold-guided demonstration-selection recipe did not establish an advantage over quota-matched random selection. Full results are supplementary. The main implication is methodological: use pose coverage to organize candidates, then verify the resulting physical behaviors.

### Result B: command conditioning helps, but cluster semantics remain unproven

On 28 selected tasks, no-command, fixed-random-group and pose-cluster students achieve 13, 17 and 17 five-second HOLD successes, respectively, under the same nominal evaluation. This is consistent with a benefit from stable conditioning, but does not distinguish meaningful pose categories from labels that disambiguate training contexts.

In the associated perturbation and contact analysis, five-second post-lift conditional survival is 62.2%, 80.0% and 74.7% for those three students. Each percentage conditions on that model's own successful lifts; it is not an unconditional task-success rate. The random-group student also has fewer interruptions in a separate matched-success comparison. Task-paired uncertainty intervals do not establish pose-cluster superiority over random grouping. These observations are limited to one training seed and correlated perturbations of the same tasks. They support testing contact behavior directly rather than assigning functional meaning to geometric labels.

### Result C: expressivity and execution do not improve together

For the matched interface comparison, a common teacher supplies 340 successful parent trajectories, split into 272 training and 68 student-held-out tasks. The students share the control architecture, action interface and an approximately matched 300-update budget. Commands come from successful teacher execution. This is a student-stage parent split, not an unseen-object test or evidence that the teacher never saw those tasks.

| Policy / interface | Grasp success | Five-second HOLD |
|---|---:|---:|
| Teacher | 64/68 · 94.1% | 54/68 · 79.4% |
| Cluster | 39/68 · 57.4% | 24/68 · 35.3% |
| Joint | 34/68 · 50.0% | 26/68 · 38.2% |
| Fingertip | 35/68 · 51.5% | 22/68 · 32.4% |
| Hybrid | 41/68 · 60.3% | 25/68 · 36.8% |

*Table 2. Matched nominal execution. Grasp requires at least 2 cm lift and sustained dual-finger object contact for 0.5 s. HOLD is evaluated from reference completion. All percentages use the same 68-task denominator.*

Hybrid obtains the most grasps, while Joint obtains the most five-second HOLD successes. No interface dominates both. Continuous targets also do not substantially improve measured fingertip adherence under this recipe. The teacher–student gap persists on training tasks, so it cannot be attributed solely to held-out generalization. Observation asymmetry, phase timing, limited optimization and command ambiguity remain plausible explanations. The current single-seed comparison identifies a bottleneck and trade-offs, not a universal best interface.

## 7. Discussion and Outlook

The evidence supports a coherent progression with an important boundary at each step. **Representation** organizes a rich motion collection into compact candidates, but pose similarity does not establish equivalent contact. **Learning** supplies physically executed demonstrations, but reference-conditioned success does not establish a reusable grasp interface. **Interface design** exposes control at several abstraction levels, but additional command coordinates do not automatically produce better execution.

This suggests three near-term priorities. First, represent the contact-establishment transition, not only a representative grasp frame, and collect multiple feasible commands for the same object and approach. Second, diagnose teacher–student disagreement on student-visited states and repeat matched interface experiments with more training seeds and optimization. Third, evaluate independently generated commands with an external wrist planner, separating command feasibility, conditional policy execution and end-to-end task success.

Remaining limitations include source imbalance, imperfect retargeting, incomplete link-level contact measurements and the privileged-to-tactile observation gap. New tools and grasp-to-in-hand transitions require explicit tests. Physical deployment needs calibrated sensing and repeated outcome measurements; qualitative feedback cannot substitute for these records. Automatic skill acquisition and Real2Sim verification remain future work.

RLDexAgents provides a working path from hand motion structure to executable, agent-callable control. Its current value is a shared representation, learning and runtime framework in which those boundaries can be tested. The next step is to make command-conditioned contact behavior reliable enough that an agent can reuse a skill beyond the reference that originally taught it.

## Supplementary Material

The [extended evidence report](supplementary_report.html) contains full dataset accounting, teacher configurations, historical distillation comparisons, expanded selection evaluation and contact-survival analysis. The [experiment log](experiment_index.md) maps claims to configurations and raw results. The [interactive gallery](pose_hoi_manifold.html) contains the complete 3D manifold, representative poses and replay videos. [Open questions](open_questions.md) list proposed verification experiments. These materials preserve the detailed evidence without interrupting the main narrative.

## References

- [@santello1998] M. Santello, M. Flanders and J. F. Soechting. Postural Hand Synergies for Tool Use. *Journal of Neuroscience*, 18(23):10105–10115, 1998. [Publication](https://pubmed.ncbi.nlm.nih.gov/9822764/).
- [@ross2011] S. Ross, G. Gordon and D. Bagnell. A Reduction of Imitation Learning and Structured Prediction to No-Regret Online Learning. *AISTATS*, PMLR 15:627–635, 2011. [Paper](https://proceedings.mlr.press/v15/ross11a.html).
- [@schulman2017] J. Schulman, F. Wolski, P. Dhariwal, A. Radford and O. Klimov. Proximal Policy Optimization Algorithms. *arXiv:1707.06347*, 2017. Preprint. [Paper](https://arxiv.org/abs/1707.06347).
- [@pinto2018] L. Pinto, M. Andrychowicz, P. Welinder, W. Zaremba and P. Abbeel. Asymmetric Actor Critic for Image-Based Robot Learning. *Robotics: Science and Systems XIV*, 2018. [Paper](https://www.roboticsproceedings.org/rss14/p08.html).
- [@ichter2023] B. Ichter, A. Brohan, Y. Chebotar et al. Do As I Can, Not As I Say: Grounding Language in Robotic Affordances. *CoRL 2022*, PMLR 205:287–318, 2023. [Paper](https://proceedings.mlr.press/v205/ichter23a.html).
