# 全量 HOI 的指尖与全手 link 接触聚类对比

日期：2026-10-26

## 目标

检验用整只手各 link 与物体的接触/距离表示，是否比只用指尖关系更适合区分 HOI 中的抓握状态。五种表示都在同一组 6,241 个参考样本、同一 `source_frame_index` 和相同的轨迹均衡权重上做 K=6 聚类。动作成败只用于聚类后的分析，没有作为聚类输入。

## 数据与特征

| 来源 | 样本 |
|---|---:|
| DexCanvas | 3,435 |
| Spider | 1,386 |
| Quick HOI | 668 |
| DexterHand | 752 |
| **合计** | **6,241** |

样本覆盖 3,185 条父轨迹、116 个物体名称。距离提取涉及 1,388 个物体碰撞资产：全部加载成功，6,241 条均有完整的 26-link 距离结果。指尖基线与全手特征使用已有关系样本选出的同一帧，不针对新表示重新挑选“更有利”的帧。

全手 link 顺序包含掌部和拇指、食指、中指、无名指、小指的关节段及指腹碰撞体。距离是基于 Sharpa URDF 与物体 USD/URDF 碰撞几何，通过 FCL 算出的最小表面间距。`near5` 表示几何间距不超过 5 mm。它是碰撞几何上的距离近似，不是原始数据的人类接触标签，也不是仿真中的真实力接触标签。

比较的五种输入：

1. `joint_only`：22 维关节角。
2. `legacy_full_relation`：原有掌部/指尖物体关系、指尖距离标签及物体形状。
3. `tip_relation_joint`：关节角 + 掌部与指尖物体关系 + 形状。
4. `link_near_joint`：关节角 + 掌部关系 + 26 个 link 的 5 mm 近接标签 + 形状。
5. `link_near_and_distance_joint`：上一项再加 26 个按物体碰撞尺寸归一化的 link 距离。

每个特征块分别标准化后按维度归一，K=6。采样权重按父轨迹均衡，避免长轨迹/多片段父轨迹在拟合中占比过高。每个方案用 3 个随机初始化检查稳定性。

## 聚类结果

| 表示 | 加权 silhouette ↑ | 重跑 ARI ↑ | cluster 与物体 NMI ↑ | 最佳簇抓起且跟踪成功率 |
|---|---:|---:|---:|---:|
| 仅关节 | 0.136 | 0.998 | 0.271 | 13.4% (229/1,698) |
| 旧版全关系 | 0.101 | 0.523 | 0.130 | 14.3% (372/2,601) |
| 指尖关系 + 关节 | 0.073 | 0.444 | **0.481** | **18.2% (143/786)** |
| 全 link 近接 + 关节 | 0.075 | 0.698 | 0.391 | 16.3% (143/875) |
| 全 link 近接与距离 + 关节 | **0.087** | **0.997** | 0.400 | 17.1% (107/624) |

完整集合有 1,165 条 `tabletop_pick_success` 和 567 条同时满足 `tabletop_pick_success`、`pose_tracking_success`，后者总体成功率为 9.1%。最佳簇成功率是簇内比率，不代表该表示总体提升了策略成功率。

`link_near_and_distance_joint` 的簇 2 和簇 5 成功率分别为 17.1% (107/624) 与 16.2% (123/761)；簇 4 几乎没有 link 在 5 mm 内，成功率 0.5% (2/374)。该方案比纯 near 标签稳定，且比指尖关系方案有更高的 silhouette；指尖关系方案的物体类别分离度及最佳簇成功率更高，但不同初始化间分簇变化较大。

## 结论

- **全手 link 距离值得加入聚类特征**：near + 距离的分群重跑 ARI 为 0.997，明显高于指尖关系方案的 0.444；其 silhouette 也从 0.073 提升到 0.087。
- **它没有全面取代指尖关系**：指尖方案对物体类别区分更强 (NMI 0.481 vs 0.400)，并得到更高的单簇成功比例 (18.2% vs 17.1%)。全手距离更稳定，但成功样本没有集中到一个明显更优的单簇。
- **单独的关节姿态形成强基线**：仅关节分群有最高 silhouette，但这说明手型自身聚类清晰，不能据此认为它更能描述功能性手物关系。加入关系特征后分群结构会改变，旧版关系权重的结果尤其不稳定。
- 因此，后续功能性聚类适合保留关节姿态，并把 26-link 接触距离作为核心关系信息；指尖/物体相对位置仍可作为补充。需要结合可视化代表样本和真实接触标签检查语义，不能只用分数选一个方案。

本次抓起/跟踪成败来自 teacher rollout 评测报告，是聚类后的外部结果。它们只表明某些几何/姿态分组与当前 teacher 的成功相关，不证明分组导致成功，也不等价于数据中每帧的接触真值。

## Manifold 浏览观察

交互式页面逐个展示五种各自 PCA 坐标系中的 6,241 点云，并把每簇到 KMeans 中心距离最小的真实样本标成星号，右侧配同帧 Sharpa hand 快照。各方法的 PC1+PC2 解释方差仅为 24.9%–38.3%，所以只能看大尺度分支和重叠，不能把二维邻近当作完整高维相似度。

- `joint_only` 的点云和簇在二维投影里更紧凑，但这是姿势空间本身容易形成分组的表现；没有手物关系时不能称为功能抓握类别。
- `tip_relation_joint` 更明显地把不同物体/手物布局分到不同流形区域（object NMI 最高），但簇间投影仍重叠，初始化之间的成员划分也不够稳定。
- `link_near_joint` 和 `link_near_and_distance_joint` 把点云拉成多条枝状带；近接 + 距离方案里有相对分离的边缘簇，同时中部区域仍有大量重叠。它重跑稳定并不意味着每个 cluster 都对应一种清楚、可命名的手势。
- 代表姿势快照中，多数簇都呈现相似的拇指对向、其他手指部分弯曲姿态，只有少数代表（例如卷曲更深或张指更明显）在视觉上容易区分。这提示 cluster 差异部分来自微小 joint/contact-distance 变化和物体布局，而不是六种完全不同的离散抓握类型。

因此浏览时建议同时看星号位置、同簇点云范围、medoid 姿势和样本物体/来源信息。需要给功能类别命名时，还应回看完整 HOI 片段及真实接触演变。

## 文件

- link-near + distance 的六类均衡 HOI 数据清单与说明（原始来源路径：`full_hoi_link_near_distance_balanced_dataset_20261026.md`）：每类 374 条，共 2,244 条。
- [按数据集来源着色的可旋转 3D manifold 浏览与分析](full_hoi_dataset_manifold_3d_20261026.md)：显示 source × cluster 分布并可逐样本检查。
- 交互式 manifold 与典型手势浏览页（原始来源路径：`../audit/functional_hand_object_clusters_20261025/full_train_hoi_6241/link_contact_clearance_comparison/manifold_review/index.html`）：可切换五种特征表示，查看完整样本投影、簇中心 medoid 在图上的位置、对应的 Sharpa 手势图和数据名。
- 方法和摘要：`summary.json`（原始来源路径：`../audit/functional_hand_object_clusters_20261025/full_train_hoi_6241/link_contact_clearance_comparison/k6_comparison/summary.json`）
- 五种表示的 PCA 对比：`method_comparison_pca.png`（原始来源路径：`../audit/functional_hand_object_clusters_20261025/full_train_hoi_6241/link_contact_clearance_comparison/k6_comparison/method_comparison_pca.png`）
- 指尖/关节方案 PCA：`tip_relation_joint`（原始来源路径：`../audit/functional_hand_object_clusters_20261025/full_train_hoi_6241/link_contact_clearance_comparison/k6_comparison/tip_relation_joint/pca.png`）
- 全手近接与距离方案 PCA：`link_near_and_distance_joint`（原始来源路径：`../audit/functional_hand_object_clusters_20261025/full_train_hoi_6241/link_contact_clearance_comparison/k6_comparison/link_near_and_distance_joint/pca.png`）
- 各方案成功样本：每个方案目录中的 `successful_examples.csv`
- 各方案中心附近代表样本：每个方案目录中的 `representatives.csv`
- 26-link 原始距离特征：`whole_hand_features.npz`（原始来源路径：`../audit/functional_hand_object_clusters_20261025/full_train_hoi_6241/link_contact_clearance_comparison/whole_hand_features.npz`）
- 聚类脚本：`compare_full_hoi_link_cluster_features.py`（原始来源路径：`../scripts/compare_full_hoi_link_cluster_features.py`）
- Manifold/手势浏览生成脚本：`build_full_hoi_cluster_manifold_review.py`（原始来源路径：`../scripts/build_full_hoi_cluster_manifold_review.py`）

聚类编号仅是算法标签，不同表示间的同号 cluster 不代表相同类别。
