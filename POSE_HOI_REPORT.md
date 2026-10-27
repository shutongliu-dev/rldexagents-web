# 手形、HOI 聚类与 PCA 技术报告

入口：[pose_hoi_manifold.html](pose_hoi_manifold.html)，同时提供 [index.html](index.html)。

可直接在浏览器打开 HTML；也可在本目录执行 `python -m http.server 8136` 后访问 `http://localhost:8136/pose_hoi_manifold.html`。

## 内容

- 6,241 条 HOI × 5 种特征表示的交互 3D PCA；可按数据集、cluster、物体着色和筛选。
- 最终 `link_near_and_distance_joint` 六类代表手形；五种方法共 30 张代表姿态图片。
- 12 条既有严格成功 demo 视频与封面、24 张普通 HOI 场景图片。
- 成功视频按 trajectory key 重新映射到最终 cluster，覆盖 C0/C1/C2/C5；C3/C4 的成功视频尚未保存。本报告明确标出此缺口。
- E1 PCA 解释方差、重建误差、Pose Bank 规模与覆盖、多样性、来源留出泛化、关节限位有效率；8 组图表均有 SVG 与 PNG。
- 完整机器可读数值、分簇清单、视频映射与原始研究记录。

## 本地资源

`assets/` 保存全部图片、视频、图表、CSS 与 JavaScript；`data/` 保存点云及数值；`sources/` 保存研究记录，记录中的图片已复制到 `assets/archive/`。原始数据/模型路径仅作来源说明，浏览报告不需要读取它们。`manifold.html` 为内嵌交互页，全部点数据直接嵌入；无 CDN 或远程资源依赖，无符号链接。

完整移动本报告时保留两个入口、`manifold.html`、`assets/`、`data/`、`sources/`。目录中的其他实验产物不属于本页依赖。

## 验证记录（2026-10-27）

- Chromium 以本地文件模式打开：6,241 点、5 方法、六类卡片加载正常。
- iframe 选点 → 代表手形详情；代表手形按钮 → 3D 点定位，两向联动通过。
- C4 无成功视频、C2 四条成功视频的筛选结果符合映射数据。
- 12 条 MP4 均为 H.264；抽样视频实际播放，duration/currentTime 正常，无媒体错误。
- 24 张普通 HOI 图片浏览入口正常。
- 390 px 宽移动端无页面横向溢出；检查期间无 JavaScript runtime 异常。
- HTML 的本地 src/href/poster 全部存在，未引用目录外资源。
- 桌面截图保存在 `assets/previews/`。

## 重新生成

`build_report.py` 从原项目现有审计产物生成报告，不重新训练或重新定义成功指标。需要 numpy 与 matplotlib，例如：

```bash
/home/ruoqu/miniconda3/envs/lab/bin/python build_report.py
```

报告中 HOI 聚类与 E1 PCA 使用不同数据口径；历史 PCA 数据还涉及不同的限位筛选、采样和加权方式。数值表使用当前机器可读结果，不能将不同口径合并解释为同一实验趋势。
