# 人手、Sharpa 与 Wuji2 手部指标及 manifold 关系

日期：2026-10-26

## 结论摘要

目前有三组相关结果：原始 HOI 人手关键点、项目 Sharpa 右手姿态，以及 Wuji Hand 2 右手姿态 retarget 到 Sharpa 后的投影。

- **人手数据的姿态变化主要沿手指张开/收拢方向。** 全量人手表示为 MCP 手坐标系中的 20 个关键点、按手长归一化后得到 60 维特征；95% 方差需要 10 个 PCA 维数。PC1 解释 59.5% 方差，并与归一化平均指尖半径相关 0.915。
- **Sharpa 姿态空间在当前数据中需要更多维度。** 22 个关节角的 95% PCA 维数为 14。六簇 silhouette 约 0.205，簇间有明显重叠，且受来源/retarget 流程影响，不能当作六种通用抓握类型。
- **Wuji2 retarget 姿态覆盖了 Sharpa 现有姿态流形的多个区域。** 1,400 个抽样姿态的平均指尖拟合误差 4.13 mm；固定 Sharpa KMeans 分配到 C0/C1/C4/C5，未形成单独孤岛。它只说明关节/手型覆盖相交，不说明 Wuji2 与 HOI 有相同的接触行为。
- **当前不能据此做完整的三手型物体交互 manifold 对比。** Wuji2 导出没有物体位姿、几何或接触标签；其通用关节列名的解剖映射仍需视频核对。现有三方结果是“人手形状统计 + Sharpa 关节统计 + Wuji2 到 Sharpa 的运动学映射”，不是三种手在统一物体任务上的对照实验。

## 数据与表示

| 手/数据 | 分析输入 | 规模与覆盖 | 适合回答的问题 |
|---|---|---|---|
| 原始人手 HOI | 20 个手部关键点；MCP 定义手坐标系；按中指链长度归一化；60 维 | 915,392 姿态样本，来自 DexCanvas、DexterHand、HRDexDB、修正腕部 HOI、OakInk Native/扩展、RoboTool | 人手手型的归一化形态、张合程度、数据源覆盖 |
| Sharpa 右手 | 22 个标准关节角；rad | 1,029,112 姿态样本，覆盖 retarget HOI、SPIDER、SharpaDex 自由手等 | 机器人关节姿态覆盖、关节簇与不同机器人数据来源 |
| Wuji Hand 2 右手 | 20 个关节角 → Wuji URDF FK 21 点掌系骨架 → DEXX Sharpa 加权运动学拟合 → 22 关节角 | 175 episodes、95,890 原始帧；每 episode 均匀抽 8 帧，共 1,400 个 retarget 姿态 | Wuji2 手型是否能由当前 Sharpa 关节模型近似、在既有 Sharpa 关节流形的位置 |

人手姿态 collection 的 129,239 个来源输入项是两个域共享轨迹与各自专属轨迹的总清单，不是 129,239 条互不重复的原始 episode。人手原始来源数按完整 collection 记录；DexCanvas 贡献了 894,856/915,392 个被分配姿态，所以解读整体分布时应优先看按来源平衡拟合的 PCA/KMeans 与来源分项，而不是把全量计数视作均匀来源抽样。

## 主要指标

### 人手与 Sharpa 全量姿态空间

| 指标 | 人手关键点 | Sharpa 关节 | 解读 |
|---|---:|---:|---|
| 输入维数 | 60 | 22 | 编码对象不同，不能直接比较原始维数 |
| PCA 达到 95% 方差维数 | 10 | 14 | 人手是在归一化点云空间，Sharpa 是关节角空间；只能各自描述内部变化复杂度 |
| PC1 方差占比 | 59.5% | 37.4% | 人手主要变化更接近单一张合方向；Sharpa 关节组合变化分散在更多方向 |
| 候选聚类数 | K=4 | K=6 | 人手 K=4 silhouette 0.227；Sharpa K=6 silhouette 0.205 |
| silhouette 候选 | K=4/6/8/12：0.227/0.193/0.173/0.186 | 0.198/0.205/0.195/0.204 | Sharpa 的 K=6 与 K=12 几乎同分，选 K=6 是控制细分，不代表天然存在六种功能抓握 |

人手聚类计数为 **404,928 / 132,930 / 353,571 / 23,963**（C0–C3）。对每簇抽取真实样本做形态统计时，C0 平均指尖半径中位数约 0.866，C3 约 0.574；拇指—食指间距分别约 0.472 和 0.215（都以人手长度归一化）。这支持 C0 较舒展、C3 较紧凑的描述；C1/C2 处于中间，但不是动作阶段或接触标签。

Sharpa 六簇计数为 **28,029 / 311,476 / 52,333 / 266,513 / 53,014 / 317,747**。FK 指尖几何抽样中，C4 拇指—食指距离中位数约 12.84 cm、平均关节绝对角约 0.108 rad，代表较张开的手型；C2 拇指—食指约 4.03 cm、平均关节绝对角约 0.688 rad，偏屈指/捏合；C0 的拇食指距离也较近，约 4.66 cm。C1/C3/C5 中 DexCanvas 较多，C0/C2/C4 中 SharpaDex 较多，说明 cluster 也反映数据与 retarget 来源。

### 自由手与 HOI 的 Sharpa 姿态差异

已在同一 Sharpa 22 关节表示下，对 SharpaDex 自由手和来源平衡 HOI 做过对比。每个 HOI 来源最多抽 1,000 帧，再从 SharpaDex 抽同样数量，每组 10,208 帧。

| 指标 | SharpaDex 自由手 | 来源平衡 HOI |
|---|---:|---:|
| 95% 方差 PCA 维数 | 9 | 14 |
| 拇指—食指距离中位数 | 6.80 cm | 7.44 cm |
| 食指—小指距离中位数 | 8.90 cm | 7.47 cm |
| 平均指尖—掌心半径中位数 | 14.82 cm | 16.90 cm |
| 组内最近邻关节距离中位数 | 0.177 rad | 0.445 rad |
| 共同 Sharpa 六簇上的 JS 距离 | — | 0.439 |

自由手与 HOI 的最近邻跨组距离中位数约 1.019 rad（自由手找 HOI）和 1.117 rad（HOI 找自由手），大于各自组内最近邻。两种姿态分布确实不同，但任务、来源和 retarget 管线同时不同；不能从这些数值推出谁更灵巧或更适合抓取。自由手中出现捏合形态也不意味着它有真实物体接触语义。

### Wuji2 retarget 与 Sharpa manifold

| 指标 | 结果 |
|---|---:|
| 原始数据 | 175 episodes / 95,890 帧 / 30 Hz |
| retarget 覆盖 | 每条均匀采样 8 帧，共 1,400 姿态；不是完整逐帧轨迹 |
| 五指指尖拟合误差均值 | 4.13 mm |
| 每个姿势平均指尖误差中位数 | 4.06 mm |
| 每个姿势最差指尖误差 P95 | 11.51 mm |
| 最差指尖误差低于 30 mm 的姿势比例 | 100% |
| 到既有 Sharpa 簇中心距离中位数 / P95 | 1.203 / 1.502（Sharpa PCA 空间） |

固定使用 2026-10-23 Sharpa PCA/KMeans，而没有把 Wuji2 加入重拟合。簇分配 C0–C5 为 **957 / 146 / 0 / 0 / 156 / 141**：Wuji2 样本落在 C0、C1、C4、C5，C2/C3 未覆盖。其最近簇中心距离中位数 1.203，落在现有来源的 0.913–1.520 范围内；P95 1.502，也在现有来源 P95 1.459–2.305 的范围内。由此可说它落在既有 Sharpa 姿态分布范围内，不能说已经匹配到特定 HOI 接触/任务 manifold。

任务之间姿势分布不同：milk-powder 任务 704 帧分布为 C0/C1/C4/C5 = 353/93/119/139；spoon-only 任务 664 帧中 C0 占 582 帧。Wuji2 提供了偏 spoon 操作的手姿样本，但因为没有物体轨迹和接触标注，暂时只能按手姿分布使用。

## 跨手结论与边界

1. **人手关键点空间与 Sharpa 关节空间的 PCA 维数不可作绝对“能力”比较。** 两边特征、归一化、数据来源均不同。人手 10 维和 Sharpa 14 维仅说明各自样本协方差结构。
2. **在人手→机器人迁移上，Wuji2 的 4.13 mm 平均指尖误差是当前直接几何证据。** 它验证采样帧的 FK 形状能被 Sharpa 近似，不验证全时序平滑、碰撞、接触力、物体操控或任务成功。
3. **现有 cluster 是数据分析索引，不应直接视为跨手通用 gesture ID。** 人手 K=4 与 Sharpa K=6 是独立拟合，编号不对应；Wuji2 采用 Sharpa K=6 的既有标签。
4. **手姿 manifold 有重叠，但物体交互 manifold 还未验证。** Wuji2 没有 3D 物体位姿、物体模型和接触标签。它无法进入已有的掌心相对物体姿态、逐 link 物体距离/接触等 HOI 特征空间。
5. **Wuji2 的 joint_0…joint_19 列名是通用名。** 当前按 Wuji Hand 2 URDF 的 thumb/index/middle/ring/pinky 顺序解释，且 URDF FK 与 angle range 合理；需要对照视频或设备元数据确认后，才把逐关节语义作为确定结果。

## 建议的下一步

- 先用少量 Wuji2 episode 对照视频检查关节顺序、左右手、关节正负方向和时序，然后再扩展到连续逐帧 retarget，增加关节速度/加速度与姿态跳变统计。
- 若要真正比较“人手 vs Wuji2 手 vs Sharpa”的几何 manifold，把三者统一到腕/MCP 掌坐标系，以掌宽或中指链长归一化，并使用同一套五指关节点/骨架特征；报告 Procrustes/关键点距离、指尖 spread、掌心半径、PCA overlap 和 source-balanced nearest-neighbor，而不要混用不同手各自 PCA 的 cluster 编号。
- 若要比较交互 manifold，Wuji2 还需要与 episode 对齐的物体位姿、物体坐标系、物体几何和可解释的接触信息。当前没有这些字段，不能从 task 文本反推接触标签。
- Wuji2 暂可作为自由手/任务相关姿态的候选补充集；训练采样时应保留数据来源与任务标签，和有物体 HOI 分开衡量。

## 图表与原始结果

- 人手全量姿态 PCA：[`human_pca_clusters.png`](../../audit/hand_pose_cluster_all_20261023/full_analysis/human_pca_clusters.png)
- 人手 cluster 姿势样本：[`human_cluster_poses.png`](../../audit/hand_pose_cluster_all_20261023/full_analysis/human_cluster_poses.png)
- Sharpa 全量姿态 PCA：[`robot_pca_clusters.png`](../../audit/hand_pose_cluster_all_20261023/full_analysis/robot_pca_clusters.png)
- Sharpa cluster 姿势样本：[`robot_cluster_poses.png`](../../audit/hand_pose_cluster_all_20261023/full_analysis/robot_cluster_poses.png)
- 自由手与 HOI 对比图：[`sharpadex_vs_hoi.png`](../../audit/hand_pose_cluster_all_20261023/sharpadex_vs_hoi/sharpadex_vs_hoi.png)
- Wuji2 投影到 Sharpa manifold：[`manifold_projection.png`](../../audit/wuji2_hand_manifold_20261026/manifold_projection.png)
- Wuji2 源手与 Sharpa retarget 骨架：[`retarget_pose_examples.png`](../../audit/wuji2_hand_manifold_20261026/retarget_pose_examples.png)
- Wuji2 逐样本分配：[`assignments.csv`](../../audit/wuji2_hand_manifold_20261026/assignments.csv)
- Wuji2 数值摘要：[`summary.json`](../../audit/wuji2_hand_manifold_20261026/summary.json)
- 原始全量人手/Sharpa 分析口径：[`ALL_HAND_POSE_CLUSTER_20261023.md`](ALL_HAND_POSE_CLUSTER_20261023.md)
- Wuji2 retarget 详细记录：[`WUJI2_HAND_RETARGET_MANIFOLD_20261026.md`](WUJI2_HAND_RETARGET_MANIFOLD_20261026.md)

