# Manifold-Guided：扩大共同评测集（2026-10-26）

状态：Teacher、Random Student、Guided Student均已完成，每位2,365条，总计7,095次episode。使用上一轮已训练的两份checkpoint，没有续训或更改选样。

## 主要结果

当前这套选样策略和训练预算下，扩大测试没有显示Manifold-guided稳定优于配额匹配随机选样。原14条小测试仍为guided 7/14、random 5/14，但更大集合上优势没有延续。

| 评测集合 | 轨迹数 | Teacher抓起保持 | Random抓起保持 | Guided抓起保持 | Guided−Random |
|---|---:|---:|---:|---:|---:|
| 全部共同任务 | 2365 | 560/2365 (23.7%) | 354/2365 (15.0%) | 343/2365 (14.5%) | -0.47 pp |
| 历史抓起＋pose成功 | 521 | 147/521 (28.2%) | 106/521 (20.3%) | 100/521 (19.2%) | -1.15 pp |
| 未参与本轮选样特征拟合 | 2333 | 532/2333 (22.8%) | 342/2333 (14.7%) | 335/2333 (14.4%) | -0.30 pp |
| 参考抬升≥2cm | 2060 | 553/2060 (26.8%) | 348/2060 (16.9%) | 335/2060 (16.3%) | -0.63 pp |
| 本次Teacher成功（补充条件统计） | 560 | 560/560 (100.0%) | 196/560 (35.0%) | 176/560 (31.4%) | -3.57 pp |
| 原14条留出任务 | 14 | 9/14 (64.3%) | 5/14 (35.7%) | 7/14 (50.0%) | +14.29 pp |

全部2,365条上，174条仅guided成功，185条仅random成功；按原始parent做5,000次配对bootstrap，差异的95%区间为[-2.13,+1.19]个百分点。历史成功521条上的区间为[-5.29,+2.90]个百分点。这些区间均跨过零；它们针对当前固定训练seed与单次rollout，不包含重新选样/训练的随机性，也不证明两种方法等效。

严格抓起＋末段pose联合成功：teacher 89、random 32、guided 14。故不能用guided较小的平均位置误差替代任务成功，或据此宣称更可控。

## 数据扩展与排除规则

从全部2,417条已有PhysX稳定接触轨迹出发，排除两组训练的40个原始parent及其52条相关轨迹，得到2,365条、1,721个parent。合并DexYCB/OakInk fixed与lifted别名。没有新增片段截断，使用每个既有descriptor的完整reference；descriptor本身已有的segment仍属于原数据定义。

其中521条有历史联合成功记录，另外1,844条是其他有接触记录的任务。32条此前参与过本轮manifold选样的特征拟合但未入选训练；单独排除后剩2,333条，结论仍无正向优势。全部命令标签沿用历史PhysX contact+joint K6，既有taxonomy本身曾利用全量数据，不能称为从未接触这些数据的zero-shot manifold实验。物体没有互斥划分，因此本次是Student训练轨迹外的泛化测试。

## 按类别的抓起保持结果

| 类别 | 条数 | Teacher | Random | Guided |
|---|---:|---:|---:|---:|
| C0 | 400 | 45 | 41 | 47 |
| C1 | 241 | 20 | 19 | 22 |
| C2 | 584 | 69 | 67 | 67 |
| C3 | 287 | 44 | 26 | 13 |
| C4 | 393 | 83 | 58 | 84 |
| C5 | 460 | 299 | 143 | 110 |

Guided在C4增加26条成功，在C5减少33条、C3减少13条；增益具有类别差异。这里C0–C5为本实验PhysX标签，不等同最新link-near或旧pose-only标签。

## 按来源的抓起保持结果

| 来源 | 条数 | Teacher | Random | Guided |
|---|---:|---:|---:|---:|
| DexCanvas | 1034 | 12 | 52 | 60 |
| DexYCB | 263 | 154 | 131 | 93 |
| DexterHand | 184 | 9 | 8 | 10 |
| HOI Full | 2 | 0 | 0 | 0 |
| HOT3D | 509 | 255 | 60 | 66 |
| HRDexDB | 140 | 74 | 49 | 63 |
| OakInk | 233 | 56 | 54 | 51 |

来源表现差异大，尤其本次Teacher在DexCanvas上的抓起保持只有12/1,034。这些任务含手内动作；统一张手启动后是否仍满足原任务的起始条件需要逐例检查。此数值只能解释为当前启动/执行协议的表现，不能外推为该Teacher在原训练初始化下的能力，也不能直接归因为数据质量。

## 小幅运动任务与误差诊断

参考抬升小于2cm的305条另统计“末段pose满足3cm/30°且双指接触保持”的指标，不要求抬升：teacher 4/305、random 7/305、guided 11/305。这些任务不全部等同手内操作，因此不把这个子组直接命名为in-hand benchmark。

总体物体位置误差的episode中位数：teacher 5.07cm、random 9.94cm、guided 9.72cm。原始均值分别27.58/14.16/11.59cm，但存在平均误差超过1m的轨迹，数量分别为1/2/1。保留原始结果且计入失败；这些极端运动/掉落案例尚未通过回放确定原因，不能只凭均值认为student优于teacher。

极端案例包括Teacher的 `oakink_native/scene_03__A004++seq__b0b131f2fc3d47f22ee3__2023-04-26-19-37-03/stage8/part0`，Random的 `dexterhand/Plate_00#segment31`、`dexterhand/Plate_00#segment99`，Guided的 `dexterhand/Cylinder_00#segment109`。

## 执行条件

Teacher仍为object-goal3200；两位Student仍为每组30条示范、60,000次teacher查询、400次更新得到的v2模型。三位模型在同一批2,365个固定资产环境中依次执行，同一reference顺序、seed42和阶段时序。每位模型前重置关节位置/速度、物体位姿/速度和输入历史。保存的两位Student初始物理状态逐项相等；与Teacher最大绝对差约1.91e-6。

纯rollout用时teacher 138.3秒、random 142.2秒、guided 142.4秒，合计约7分钟，不含Isaac与资产初始化。2,365条/模型的指标均为有限数值。所有评测进程已退出。

抓起保持定义沿用小规模实验：抬升至少2cm且双指物体接触持续0.5秒，末段30步中抬升保留至少80%、双指接触至少50%。严格pose成功额外要求末段至少80%的帧满足3cm/30°。RELEASE仍由共同runtime直接张手，不用于判断网络是否学会释放。此次没有增加指令切换、触觉扰动、训练seed或重复rollout测试。

## 当前结论与后续方向

当前证据不足以支持“几何/接触manifold覆盖选样能提升抓握成功率”的贡献。选样空间覆盖变好，但效果没有稳定转化为任务收益。应先检查C3/C5的选中示范是否存在闭合时序、接触建立方式或teacher动作冲突；再用相同预算增加配对训练seed验证。动作时序一致性可能比仅扩大静态pose覆盖更重要，这是待检验的解释。

## 产物

- [结构化全量对比](../../audit/manifold_selection_probe_20261026/expanded_comparison.json)
- [2,365条评测清单](../../audit/manifold_selection_probe_20261026/expanded_inputs_v1/rows.json)
- [Teacher逐任务结果](../../audit/manifold_selection_probe_20261026/expanded_eval_v1/teacher/episodes.json)
- [Random逐任务结果](../../audit/manifold_selection_probe_20261026/expanded_eval_v1/random/episodes.json)
- [Guided逐任务结果](../../audit/manifold_selection_probe_20261026/expanded_eval_v1/guided/episodes.json)
- [原快速训练报告](manifold_guided_quick_probe_20261026.md)

运行脚本：`scripts/prepare_manifold_expanded_eval.py`、`scripts/rsl_rl/run_manifold_selection_probe.py --mode pair`、`scripts/summarize_manifold_expanded_eval.py`。远端目录：`/mnt/cpfs/workspace/rq_ws/outputs/manifold_selection_probe_20261026/expanded_eval_v1/`。
