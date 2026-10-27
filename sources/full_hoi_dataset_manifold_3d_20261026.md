# Full HOI datasets on 3D cluster manifolds

日期：2026-10-26

## 3D 浏览器

打开可旋转的 3D manifold 浏览页（原始来源路径：`../audit/functional_hand_object_clusters_20261025/full_train_hoi_6241/link_contact_clearance_comparison/manifold_3d_review/index.html`）。页面默认打开当前关注的 `link_near_and_distance_joint`，也可以切换到其余四种表示。

- 鼠标拖动旋转、滚轮缩放；悬停显示 key/source，点击固定样本详情。
- 默认按 key 前缀识别原始数据集来源，可在 **Original dataset / Training collection kind / Cluster** 三种颜色之间切换，并筛选来源和 cluster。
- 星号标出每个 cluster 的典型 medoid 样本；右侧表格显示来源 × cluster 数量。
- 点上显示的是同一批 6,241 条 HOI reference sample。不同特征方法各自拟合 PCA，坐标轴不跨方法对齐；为了方便旋转查看，三个 PC 坐标分别除以各自标准差，hover 详情保留未缩放 PCA 坐标。

先前页面按训练集合的 `kind` 字段着色，把 HOT3D、DexYCB、OakInk lifted、HRDexDB 合并在 `spider`，把 OakInk native 合并在 `quick_hoi`，所以看起来像没有这些数据。新页面从 reference key 前缀识别更细的原始数据集来源，并同时保留 `kind` 颜色选项。

| 原始数据集 | 全量样本数 |
|---|---:|
| DexCanvas | 3,435 |
| DexterHand | 752 |
| HOT3D | 798 |
| DexYCB | 322 |
| OakInk（native + lifted） | 672 |
| HRDexDB | 194 |
| OakInk (wrist-adapted) | 68 |
| **合计** | **6,241** |

## DexCanvas 网格状分布的来源检查

3D 页新增了 `DexCanvas preparation lineage` 和 `Object model` 两个着色方式，便于检查这类图形是否与补充批次或离散物体模型对应。当前 3,435 条 DexCanvas manifold 样本由两条准备路径组成：

| 准备路径 | 样本 | 独立 parent | C0 | C1 | C2 | C3 | C4 | C5 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| General 50g | 1,600 | 1,048 | 697 | 363 | 126 | 109 | 305 | 0 |
| In-hand expansion | 1,835 | 635 | 1,036 | 701 | 78 | 4 | 14 | 2 |

查阅项目里的 DexCanvas expansion 数据准备记录，并核对样本 descriptor/reference 路径后，当前结果支持以下判断：

- `dexcanvas_inhand_expansion_20261016` 的 1,835 条来自已有 DexCanvas 官方 train 窗口；脚本对 49,431 个 train 窗口做阶段和手物相对运动分类，再按物体/运动类型/capture 选出新增窗口。没有生成新的完成轨迹，reference 仍指向原 `dexcanvas_sharpa_right_v1` 训练轨迹。
- 旧的 General 50g 1,600 条同样引用 DexCanvas retarget train trajectory，并带连续拟合、速度和物体有效窗口筛选描述；它们不是本次新做的 teacher completion。
- 扩展批次在聚类上高度集中于 C0/C1（1,737/1,835），而 General 50g 主要落在 C0/C1/C4。可是 DexCanvas 内 preparation lineage 与 cluster 的 NMI 只有 0.095，lineage silhouette 在完整特征空间/三维 PCA 分别为 0.027/0.016，两个 lineage 并没有形成清楚分离的独立流形。
- DexCanvas 内 cluster 与 object identity 的 NMI 为 0.392，明显高于 lineage NMI。这说明图形与离散物体类别/碰撞形状的关联比“来自扩展批次还是旧 General 清单”的关联更强；但它还不能单独证明网格结构就是由 object shape 导致。

因此，**目前没有证据支持把网格状分布归因于生成补全**。更可能的解释是 object 模型类别、原始 reference 的动作/姿态组合，以及扩展集按 in-hand 运动类型筛选后造成的样本比例共同作用。3D 页里可过滤 DexCanvas 后切换 `DexCanvas preparation lineage` 或 `Object model` 颜色，直接检查两种着色是否沿网格条带分离。

## 观察结果

| Manifold 特征 | 前三主成分解释方差 | Cluster 与原始数据集 NMI | 数据集 silhouette：原特征 | 数据集 silhouette：PCA-3 |
|---|---:|---:|---:|---:|
| 仅关节 | 49.6% | 0.308 | 0.064 | 0.056 |
| 旧版全关系 | 41.3% | 0.072 | -0.117 | -0.225 |
| 指尖关系 + 关节 | 31.9% | 0.252 | 0.024 | -0.100 |
| 全 link 近接 + 关节 | 32.0% | 0.214 | 0.056 | -0.049 |
| **全 link 近接 + 距离 + 关节** | **33.8%** | **0.218** | **0.050** | **-0.076** |

Dataset silhouette 用 2,000 个固定随机抽样点估算；接近 0 表示不同来源的点分布大量重叠，负值表示同来源点并没有在该空间中形成更紧凑的分组。NMI 看的是 cluster 与来源标签的关联度，与 silhouette 测量的几何分离不是同一指标。当前 link-near + distance 的训练集合 kind NMI 为 0.242，细分为原始来源后 NMI 为 0.218。

对当前的 link-near + distance manifold，前三维保留 33.8% 的特征方差；原始数据集 silhouette 在全特征空间为 0.050，在三维投影为 -0.076。因此来源总体大量混合，三维投影还会把部分来源进一步叠在一起。但局部 cluster 有明显来源集中：Cluster 3 有 286/644 条 OakInk，Cluster 4 有 319/374 条 DexCanvas，Cluster 5 有 409/761 条 HOT3D 和 162 条 DexYCB。DexYCB、HOT3D、OakInk 和 HRDexDB 都实际包含在全量数据中。浏览页可单独筛选这些数据集，检查它们在流形中的位置及和其他来源的重叠。

这说明全局几何结构没有被来源简单分开，但一些 cluster 仍带明显数据来源偏差。它可能来自手势和物体差异、reference 处理方式或资产碰撞几何差异；本可视化本身不能判定是哪一种原因。cluster 是同一 PCA 特征空间上的 KMeans 结果，source 标签只用于着色和统计。

## 文件与生成方式

- 可旋转 3D HTML（原始来源路径：`../audit/functional_hand_object_clusters_20261025/full_train_hoi_6241/link_contact_clearance_comparison/manifold_3d_review/index.html`）
- 3D PCA 指标摘要（原始来源路径：`../audit/functional_hand_object_clusters_20261025/full_train_hoi_6241/link_contact_clearance_comparison/manifold_3d_review/summary.json`）
- 浏览页生成脚本（原始来源路径：`../scripts/build_full_hoi_dataset_manifold_3d.py`）

该页面为本地自包含 HTML，无需起 Viser 服务或加载仿真器。
