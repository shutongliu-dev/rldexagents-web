# Concise RLDexAgents narrative

Story: diverse hand motions → structured pose space → representative skill candidates → physical RL interactions → interface-conditioned students → agent-callable tools.

| Section | Reader question | Main evidence / visual |
|---|---|---|
| Abstract | What is the method and the central finding? | ~150-word synthesis |
| 1 Introduction | Why is a pose not yet an executable agent skill? | Figure 1: complete story |
| 2 From Hand Motions to Pose Manifolds | What structure exists, and how does it organize candidates? | Figure 2: data scale, source projection, variance, six medoids |
| 3 Learning Executable Dexterous Skills | How does physical RL turn references into demonstrations? | Teacher, adaptation, success filtering; detailed recipes supplementary |
| 4 Interface-Conditioned Skill Distillation | Which information does each command retain or omit? | Figure 3: four commands and common learning path |
| 5 An Extensible Toolkit for LLM Agents | How does the agent delegate finger control? | Figure 4: supported API flow + documented simulation sequences |
| 6 Experiments and Key Findings | What do the main comparisons establish? | Table 1: representation; short conditioning result; Table 2: matched interfaces |
| 7 Discussion and Outlook | What remains between this pipeline and reusable dexterity? | Three insights and next experiments |

Four main figures and two tables. Full checkpoint identities, population accounting, phase variants, expanded selection tests and contact survival remain in `supplementary_report.html`, `RLDexAgents_Supplementary_Report.md` and `experiment_index.md`. The main report links these rather than repeating their contents. The complete interactive manifold and video gallery remain available on demand.

Core insights:
1. Structured geometry improves organization, not automatic manipulation equivalence.
2. Successful physical RL interaction is the bridge from pose to executable demonstration.
3. Interface expressivity and distillability trade off; more coordinates do not guarantee better control.
