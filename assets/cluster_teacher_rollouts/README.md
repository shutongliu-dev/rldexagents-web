# 六类最新 Cluster 的 Teacher HOI Rollout（Isaac Sim）

General teacher `model_5200.pt` 在 Isaac Sim 中闭环执行；腕部沿 HOI reference，手指由 teacher 控制。每类包含 30 fps MP4、初始/首次抬升/结尾快照及逐帧状态/action NPZ。

六条视频统一使用白色桌面与浅灰色物体渲染。C1、C2、C4 已替换为不同轨迹；C0、C3、C5 保留原轨迹并按统一材质重新渲染。被替换或重渲染前的版本保存在 `previous_versions/`。

| 类别 | HOI key | 抬起 | 稳定 HOLD | 峰值指尖力 | >20 N 时间占比 |
|---:|---|---|---|---:|---:|
| C0 | `dexycb_lifted/dexycb_02_right_011_banana_20200813_152647_00` | 是 | 是（100%） | 19.34 N | 0.0% |
| C1 | `dexycb_lifted/dexycb_07_right_025_mug_20200928_154547_00` | 是 | 是（100%） | 27.69 N | 1.6% |
| C2 | `hrdexdb_24f/toothbrush_holder-3` | 是 | 是（100%） | 37.13 N | 0.7% |
| C3 | `dexcanvas/traj_00021628#segment0` | 是 | 是（100%） | 19.04 N | 0.0% |
| C4 | `oakink_lifted/oakink_0005_right_A16013_00` | 是 | 是（100%） | 21.22 N | 2.3% |
| C5 | `hot3d_v2/aria_P0001-b2bcbe28_right_whiteboard_marker_00` | 是 | 是（100%） | 19.82 N | 0.0% |

## 浏览与数据

- [视频与快照浏览页](index.html)
- [六类 lift snapshot 总览](contact_sheet.jpg)
- [逐类轨迹与指标 manifest](manifest.json)
- `videos/`：每类一个 MP4。
- `snapshots/`：初始、首次稳定抬起、结束画面。
- `trajectories/`：逐帧 `hand_q`、`wrist_q`、`object_pose`、接触力、`teacher_action` 与 `phase`。

稳定 HOLD 判据：最后 30 个仿真 tick 内物体抬升至少 2 cm，且至少两个目标物接触指尖达到 0.5 N 的帧占比不低于 95%。力值来自对应的实际 Isaac Sim 重放。
