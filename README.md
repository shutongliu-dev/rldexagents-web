# RLDexAgents Web Report

A self-contained research website for **An Extensible Dexterous Skill Toolkit for LLM Agents**. This repository includes the technical report, interactive hand-pose and HOI manifold, figures, color demonstration videos, source documents, and bundled experimental evidence.

## Project page

**Live website:** https://shutongliu-dev.github.io/rldexagents-web/

GitHub Pages publishes the static website from the root of `main`. The source repository remains private; the deployed project page is publicly accessible.

## View locally

Open `index.html` for the main report, `pose_hoi_manifold.html` for the English interactive gallery, or `supplementary_report.html` for the extended evidence report.

For a local web preview, run this command from the repository directory and open <http://localhost:8000>:

```sh
python -m http.server 8000
```

The website is static. Viewing it requires no build step, CDN, or external image/video service; fonts and media are included.

## Contents

| Path | Contents |
| --- | --- |
| `index.html` | Main report |
| `pose_hoi_manifold.html` | English gallery, cluster representatives, videos, PCA and pose-bank analysis |
| `manifold.html` | Interactive 3D manifold viewer |
| `supplementary_report.html` | Extended evidence report |
| `assets/`, `figures/` | Local page styles, scripts, fonts, figures and media |
| `HOI_videos/` | Original color demonstration recordings |
| `assets/cluster_teacher_rollouts/color_trimmed/` | Display clips matched to the original video frame counts |
| `data/`, `evidence/`, `sources/` | Numeric results, provenance and supporting records |
| `*.md`, `*.tex`, `references.bib` | Report sources and references |

## Editing

Saved HTML and assets are the current distributable website. Python builders and presentation helpers are included for provenance. Some historical builders also require the original training/audit workspace; viewing or editing the shipped pages does not require it.

Original recordings and evidence remain included. Color presentation media is tracked separately from original rollout measurements. The hidden shortcut row remains in the main page markup and can be restored later.

The repository includes large local videos and is intended to preserve the complete website package. The project page is hosted on GitHub Pages.

## Evidence scope

The reports document the Sharpa right-hand setup and the recorded evaluation protocols. Selected teacher examples are not aggregate agent success rates or quantified real-robot results.

<details>
<summary>Original report index</summary>

# 技术报告索引

这里保存从训练、蒸馏、手姿表示与 Agent 接口实验中整理出的阶段性技术结论。报告只收录有明确实验记录支撑的发现，同时标记实验范围、限制和仍未回答的问题。

## RLDexAgents 研究报告

- [HTML 主入口](index.html)
- [精简主报告 Markdown](RLDexAgents_Technical_Report.md) / [LaTeX 源码](RLDexAgents_Technical_Report.tex) / [参考文献](references.bib)
- [制作与验证记录](production_checks.md)

- [扩展证据与历史实验补充报告](supplementary_report.html) / [补充报告 Markdown](RLDexAgents_Supplementary_Report.md)

主报告按一条方法故事线组织，包含七节、四张主图、两张核心表。首页 Figure 1 使用 [method.pdf](method.pdf)，上部默认展开带数据来源筛选的交互 manifold。完整实验口径与复现记录移至补充材料。

## 综合结论

- [灵巧手 policy 接口、蒸馏与手姿 Manifold 的实验结论（2026-10-27）](SYSTEMATIC_FINDINGS_20261027.md)

## 研究专题与可视化

- [手姿、HOI 聚类与 PCA 技术报告](POSE_HOI_REPORT.md)：交互 Manifold、代表姿态、成功轨迹和数据分析图表；浏览入口见 [pose_hoi_manifold.html](pose_hoi_manifold.html)。

综合报告记录适用于当前 Sharpa 手、数据版本及对应评测协议，不自动代表真机部署性能或任意新物体泛化能力。

</details>
