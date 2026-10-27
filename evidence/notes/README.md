# System0 数据盘点（2026-10-23）

本文只统计可在本机或集群上核对的原始数据、Sharpa 适配结果和训练清单。**原始序列、retarget 轨迹、连续窗口、任务阶段、自由手 segment、仿真环境槽位不是同一计数单位，不能跨列相加。** 同一个 OakInk 源序列还可能出现在 SPIDER、修正腕部 HOI 和 OakInk Native 三条派生链中。

## 1. 最新训练实际读取什么

当前运行的 `full_hoi_object_pose_force_curriculum_20261023` teacher，以及其起点 `full_hoi_object_pose_posttrain_20261022/train_patchfix/model_3200.pt`，读取同一份 [HOI 清单](#权威清单与路径)：**6,241 条唯一右手、有物体的 Sharpa reference**。当前 teacher 的 `params/sequences.json` 是 8,192 个仿真环境槽位、6,241 个唯一 descriptor；剩余 1,951 个槽位是重复分配，不是新轨迹。其实际槽位分配为 SPIDER 1,413、修正腕部 HOI 438、DexCanvas 4,055、DexterHand 790、OakInk Native 1,496。奖励只计算物体目标；**当前 teacher 不加载自由手**。

| 最新 HOI 来源 | 唯一 reference | 数据形态与手部适配 | 物体资产 |
|---|---:|---|---|
| SPIDER 派生的五类右手 HOI | 1,386 | 已有 Sharpa 右手轨迹 | 1,386 个 descriptor 均指向存在的 USD |
| 修正腕部的人手 HOI | 68 | 84 条右手 Sharpa 快速 retarget 中被选入的部分 | 68 个 descriptor 指向存在的 URDF |
| OakInk Native 阶段 | 600 | 原始人手阶段经 Sharpa retarget | 600 个 descriptor 指向存在的 USD |
| DexCanvas | 3,435 | Sharpa 右手 retarget 后的连续窗口 | 3,435 个 descriptor 指向存在的 USD |
| DexterHand | 752 | Sharpa 右手 retarget 后的连续窗口 | 752 个 descriptor 指向存在的 USD |
| **HOI 合计** | **6,241** | **全部有物体；全部进入当前 teacher 清单** | **所有选中资产路径存在** |

当前掌心系指尖 student 的全量 teacher collection / DAgger 也以这 6,241 条 HOI 为任务池；蒸馏实际可用的动作行数还受 teacher rollout 和阶段筛选影响，**不能把 6,241 说成成功示范数**。`full_hoi_pooled/catalog.json` 为每条 HOI 建了 3 个机器人指尖锚点；其中 4,855 条另有合格的人手配对指尖，剩余 1,386 条 SPIDER 没有人手等效锚点。锚点不是独立轨迹。

较早的全量**混合**清单 `tactile_goal_posttrain_20261021/full_train_single_gpu/train_8192.json` 有相同 6,241 条 HOI，另有 1,951 个 SharpaDex 自由手**场景槽位**。这些槽位只对应 488 个静态来源 segment，重复的 `dynamic_slot` 在启用动态池的训练中可于 reset 时重采样。早先 T1a 混合训练的四个 rank 的 `sharpadex_coverage.json` 均记录访问了完整的 12,771 个自由手 segment；它与当前只用 HOI 的物体奖励续训是两种数据配置。

## 2. 原始数据、retarget 与未使用量

下表的“未使用”均针对**当前 6,241 条 HOI teacher**。历史模型曾用过其中一些数据，不能把“本轮未使用”理解为“从未使用”。

| 来源 | 原始／完整候选池 | 已有 Sharpa 适配 | 本轮使用 | 本轮未使用或尚未准备 |
|---|---|---|---:|---|
| **SPIDER 右手五类** | 本地 `/data/spider_sharpa/processed/`；DataEngine 镜像中有 1,757 个右手候选目录 | 1,757/1,757 目录均有 `0/trajectory_mjwp.npz` | 1,386 | **371** 个候选未选入；分来源见下表。原始 HOT3D/DexYCB 等数据集不在这里另算一次。 |
| **修正腕部 HOI** | RoboTool/OakInk 派生人手 reference **152** 条：右 84、左 68；旧 `hoi_full_20261010` 61 条与修正版重叠 | 右 84/84 已有 `reference_pose.npz`；左手未接入右手环境 | 68 | 右手 **16** 条已 retarget 但未选；左手 68 条不适用于当前右手模型。 |
| **OakInk Native** | OakInk-v2 **627** 个原始 annotation、**2,840** 个阶段；严格旧筛选为仅右手单物体 **716** 阶段，扩展筛选另有右手单目标 **1,164** 阶段 | 旧批次 **711** 阶段、新批次 **1,164** 阶段已生成 Sharpa reference；旧批次 5 阶段的源 annotation 缺目标物体位姿 | 600 | 旧批次 val 58 + test 53 = **111** 阶段未训练；新增 1,164 条也尚未进入当前 teacher。与修正腕部 HOI 和 SPIDER OakInk 存在源序列重叠，不能直接相加当独立人类示范。详见[覆盖检查](HOI_RETARGET_COVERAGE_20261023.md)。 |
| **DexCanvas** | 原始 **111,857** 条轨迹、894 个 parquet shard；已全部完成右手 retarget | 冻结的旧窗口清单来自当时 21,918 条 retarget 轨迹，生成 **61,822** 个连续窗口：train 49,431 / val 6,159 / test 6,232；完整原轨迹另进入[姿态聚类](ALL_HAND_POSE_CLUSTER_20261023.md) | 3,435 个 train 窗口 | 同一冻结 train 清单还有 **45,996** 个未用窗口，val/test 共 **12,391** 个未训练窗口；其余 **89,939** 条已 retarget 原轨迹未进入该旧窗口快照。窗口与原轨迹单位不同，不能相加。 |
| **DexterHand** | 8 个源 session 的 15 份 NPZ（多数各有 20/60 FPS，不能重复算 session） | 8 个 session 都有右手 retarget，另有 8 个左手 retarget；右手窗口清单仅覆盖 7 个 session，共 **997** 窗口 | train **752** 窗口 | train 窗口无遗漏；val 90 + test 155 = **245** 窗口未训练。`RubiksCube_00` 虽有右手 retarget，但未纳入这 7-session 窗口清单；左手适配也未用于右手 teacher。 |
| **SharpaDex 自由手** | 测量的右手关节序列整理为 **12,771** 个连续 segment、10,113,608 源帧 | 原生 Sharpa q，无人手→机器人 retarget；物体标签在自由手训练中去除 | 当前物体 teacher **0** | 本轮 12,771 segment 均不进入 HOI teacher；早先混合 T1a 通过动态池访问了全部 12,771。1,951 个 manifest 槽位不能从 12,771 中直接相减。 |

SPIDER 五类的候选/使用/未用明细均以 DataEngine `processed/<source>/sharpa/right/<case>/0/trajectory_mjwp.npz` 的 case 目录和本轮 descriptor key 核对：

| SPIDER 子来源 | 有适配候选 | 本轮使用 | 本轮未用 |
|---|---:|---:|---:|
| DexYCB fixed | 145 | 113 | 32 |
| DexYCB lifted | 259 | 209 | 50 |
| HOT3D v2 | 1,016 | 798 | 218 |
| HRDexDB 24f | 246 | 194 | 52 |
| OakInk lifted | 91 | 72 | 19 |
| **合计** | **1,757** | **1,386** | **371** |

DataEngine 还保存 **89** 个 `dexycb_grounded` 适配目录，以及 `rollout_refs` 58、`rollout_refs_89` 68、`rollout_refs_clean` 58 个适配目录；它们都未进本轮清单，且是替代/派生版本，不加到上表的 1,757 个原始候选里。

## 3. 其他现有数据与计数边界

- **HRDexDB 人手原始库：** DataEngine 的 `data/hrdexdb_human/metadata/episodes.parquet` 有 **2,104** 行，其中人手 episode **441** 条。SPIDER/HRDexDB 的 246 个 Sharpa 目录已与其中 246 个原始 ID 精确对应，但各只有 20 帧；另外 195 个 ID 没有 SPIDER 目录，其中 **194 条已补齐完整 Sharpa retarget**，1 条缺源文件。人手聚类可读取其中 429 条源手关节目录。详见[覆盖检查](HOI_RETARGET_COVERAGE_20261023.md)。不能用 2,104 − 194 宣称“未使用人手 episode 数”。
- **RoboTool 本地库：** `/home/ruoqu/crq_ws/dexx/sharpa_tac_rl/data/robotool_batch/` 有 61 个一级目录，含不同任务录制、旧 `hoi_full_20261010` 61 条、修正腕部人手 152 条，以及 `models/` 的 57 个一级物体资产目录。除上述 68 条已选修正腕部 HOI，其他 RoboTool 任务未在本轮清单；任务录制格式不统一，未把目录数冒充 episode 数。`/data/robotool/` 是另一个较大的原始库，不与这些导出结果相加。
- **历史仿真执行：** DataEngine `data/local_system0_20261011/history/` 的三组 `dexs0_rollouts*` 共 **984** 个 NPZ（396 + 356 + 232）；另五个按来源命名的历史目录合计 **480** 个 NPZ。这些是已有执行/导出产物，不是本轮 6,241 条参考输入，也不当作新的原始人手数据。
- **资产不能替代 reference：** DexCanvas 22 类物体已有 USD/CoACD（154 个 convex collider）；本轮 HOI descriptor 的物体资产路径均可访问。资产数量、有效碰撞和物理任务成功是不同问题。OakInk Native 的 5 个准备失败阶段仍需单独修复资产/映射。

## 权威清单与路径

| 用途 | 路径 |
|---|---|
| 当前 teacher / student HOI 唯一清单 | `/mnt/cpfs/workspace/rq_ws/outputs/grasp_lift_gesture_distill_v1_20261022/full_hoi_dagger/all_hoi.json` |
| 当前 teacher 实际 8,192 场景分配 | `/mnt/cpfs/workspace/rq_ws/outputs/full_hoi_object_pose_force_curriculum_20261023/train/params/sequences.json` |
| 上一轮混合 8,192 清单 | `/mnt/cpfs/workspace/rq_ws/outputs/tactile_goal_posttrain_20261021/full_train_single_gpu/train_8192.json` |
| SPIDER 右手适配 | `/mnt/cpfs/workspace/DataEngine/data/local_system0_20261011/hoi/spider/processed/` |
| 修正腕部右手适配 | `/mnt/cpfs/workspace/DataEngine/data/local_system0_20261011/hoi/human_wrist/retarget_right84/` |
| OakInk 原始与 Native 适配 | `/mnt/cpfs/workspace/DataEngine/data/local_system0_20261011/raw/oakink_v2/`；`/mnt/cpfs/workspace/rq_ws/outputs/oakink_native_preparation_20261017/` |
| DexCanvas 原始、retarget、窗口 | `/mnt/cpfs/workspace/DataEngine/data/dexcanvas/`；`/mnt/cpfs/workspace/DataEngine/data/retarget/dexcanvas_sharpa_right_v1/`；`/mnt/cpfs/workspace/DataEngine/references/dexcanvas_sharpa_v1/` |
| DexterHand 原始、retarget、窗口 | `/mnt/cpfs/workspace/DataEngine/data/dexterhand/`；`/mnt/cpfs/workspace/DataEngine/data/retarget/sharpa_right_v1/`；`/mnt/cpfs/workspace/DataEngine/references/dexterhand_sharpa_v1/` |
| SharpaDex 动态自由手池与历史实际覆盖 | `/mnt/cpfs/workspace/rq_ws/outputs/sharpadex_full_pool_20261019/`；`/mnt/cpfs/workspace/rq_ws/outputs/tactile_goal_posttrain_20261021/t1a_train/{sharpadex_coverage.json,rank*/sharpadex_coverage.json}` |

计数方法：直接解析两个训练 JSON manifest 和 descriptor 的 `kind/key/reference/object_usd/object_urdf`；将当前 HOI key 与各来源候选 key 比较；读取 DexCanvas/DexterHand/OakInk/SharpaDex 的数据汇总及 split JSON；DexCanvas retarget 完成后核对 `status.json` 的 **894/894** 个 shard 与 **111,857/111,857** 条轨迹。未对原始多模态帧做新的物理质量评定。

## 2026-10-23 retarget 补齐进展

- **当前训练清单无 retarget 缺口：** 上述 6,241 条 HOI 的 reference 均已存在。未被选进训练的 SPIDER 371 条、修正腕部右手 16 条、OakInk Native 111 条验证/测试阶段和 DexterHand 验证/测试窗口也已有适配结果；这些是“未训练”，不是“未 retarget”。
- **DexCanvas 原始库补齐完成：** 原任务于 2026-10-12 在 527/894 个完整 shard 后中断，已有 67,107 条完整轨迹。2026-10-23 在 DSW `:1002` 恢复同一输出目录的 `scripts/retarget_dexcanvas.py`，复用了已完成 shard；2026-10-24 **00:44** 达到 **894/894 个完整 shard、111,857/111,857 条轨迹**，`status.json` 为 `complete` 且失败字典为空。输出目录为 `/mnt/cpfs/workspace/DataEngine/data/retarget/dexcanvas_sharpa_right_v1/`，日志为 `/mnt/cpfs/workspace/DataEngine/reports/dexcanvas_sharpa_right_retarget_resume_20261023.log`。这些新轨迹进入[全量姿态聚类](ALL_HAND_POSE_CLUSTER_20261023.md)，**没有自动加入当前 6,241 条 teacher 训练清单**。
- **OakInk Native 5 个阶段无法从现有源标注补齐：** 对原始 annotation 逐条检查，所标注物体 ID 都不在该序列的 `obj_transf` 中。其中 `O02@0094@00003` 还缺 repaired visual/CoACD 资产；`O02@0033@00001` 和 `O02@0033@00002` 虽有资产，但在各自失败序列中缺对应物体位姿。相邻 ID 属于不同物体（搅拌棒/玻璃棒），不能代替目标。已在 `prepare_oakink_native_references.py` 将原来的含糊 `KeyError` 改为明确的缺失变换错误。现有 711 个成功阶段不受影响。
- **HRDexDB 新增完整轨迹已做运动学适配：** 441 个人手 episode 中有 246 个 ID 精确对应 SPIDER 右手目录，但每个只有 20 帧；另 195 个 ID 没有该目录，其中 194 个已补齐完整 Sharpa 轨迹，1 个源目录缺失。新轨迹尚未完成统一物体 USD／碰撞和物理可行性接入，不能把它们算进当前 teacher 的 6,241 条训练清单。详见[覆盖检查](HOI_RETARGET_COVERAGE_20261023.md)。
