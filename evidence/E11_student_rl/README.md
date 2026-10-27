# C student：object-reward PPO 400

**状态：可用（2026-10-26，按用户决定登记）。** 保存的权重为 `student.pt`，原 C0–C5 student 的 object-reward PPO 续训版。可用状态表示保留供部署试用，不表示所有物体、空间姿态均验证成功。本次归档未执行真机动作。

本目录保留权重和实验记录副本。现已本地接入 `dex_agent.system0.ClusterGraspTool`，并将运行时需要的权重实际复制进包；见 [工具说明](../../docs/cluster_grasp_tool.md)。本地工具提供cluster/phase命令及宿主反馈推理，不发送硬件命令。下述旧部署入口属于来源项目，不是新工具运行依赖。

## 输入与输出

30 Hz，GRU读取最近8帧，每帧117维：

| 字段 | 维度 |
|---|---:|
| 实测手指关节角（rad） | 22 |
| 实测关节速度（rad/s） | 22 |
| 上一步归一化动作（EMA前） | 22 |
| 掌心系线速度、角速度（m/s、rad/s） | 6 |
| 五指尖力，传感器局部系 | 15 |
| 同一组五指尖力，掌心系 | 15 |
| 五指尖力有效位 | 5 |
| C0–C5类别one-hot | 6 |
| FORM/HOLD/RELEASE one-hot | 3 |
| 阶段时长，截断5秒后除以5 | 1 |

力按每轴±40N裁剪，除以10N输入。无物体观测、绝对腕部位置/朝向、q_seed、目标指尖或未来轨迹。C0–C5是既有类别编号，不对应未经验证的语义手型名称。

输出22维归一化手指动作，按权重内scale/offset解码为绝对关节位置，再做一次EMA（alpha=.4）和真实关节限位。运行时返回弧度制关节目标；不要重复解码/平滑。腕部由外部控制。RELEASE由运行时给明确张手目标，再经过同样的EMA与限位。

## 训练与已有证据

从原始28条精选DexYCB的C student初始化，在原28条及squeegee_2、yellow_hammer_1、yellow_hammer_2共31条上训练。496环境，400次PPO更新，约19分09秒。仅物体任务与安全正则奖励，无DAgger或手指reference tracking；student观测保持不变。训练使用真实手限位、5秒末段HOLD、±2cm平移和±10°yaw扰动。

下表针对原28条，每条件每任务一次闭环执行：

| 指标 | 原位：原C→本版 | 空间扰动：原C→本版 |
|---|---:|---:|
| 短时成功 | 21→21 | 21→21 |
| HOLD末5帧成功 | 13→14 | 13→15 |
| 完整5秒保持 | 5→8 | 7→7 |
| 出现保护触发 | 1→2 | 1→2 |

短时成功要求HOLD阶段连续5帧满足条件；原28条的条件是抬升超过2cm且至少双指有效力≥1N、无保护故障。工具条件改为物体误差<3cm/30°且双指有效接触。三条工具的末尾保持仍为0/3；squeegee仅在空间扰动下出现短时成功。改善和退化并存，未证明任意新工具可抓。

`*_results.json`为逐任务结果；`deploy_smoke.json`记录六类×三阶段、共540帧离线部署推理，验证22维有限输出和限位。输入为零力合成反馈、关节跟随目标，不是物理仿真或真机抓握测试。

## 使用现有部署入口试用

在来源项目 `dexhand_hoi_learning` 根目录运行，显式将本目录的 `student.pt` 路径填入参数：

```bash
# 只读真实传感器并打印目标
bash scripts/run_cluster_student_live.sh --checkpoint /path/to/student.pt

# 现场准备好后，实际发送手指目标
bash scripts/run_cluster_student_live.sh --checkpoint /path/to/student.pt --send
```

来源项目的本机快捷脚本配置了既有SDK/设备；换机器须使用显式设备配置的Python入口 `scripts/deploy_cluster_student.py`，不要照搬设备设置。依赖及SDK安装按来源项目 `docs/deploy/cluster_student.md`。

输入命令并按Enter：`0`–`5`开始对应FORM，`h`进入HOLD，`r`张手，`f`返回FORM，`s`停止推理并保持最近实测位置，`q`退出。`s`不是硬件急停。

快捷脚本是固定腕部模式（局部速度置零），不能用于移动腕部测试。腕部运动时改用Python入口的 `--live-arm-bridge HOST`，提供真实局部速度。交互入口需要手动进入HOLD，与仿真自动双指接触切换HOLD不同；试用时记录切换时刻。

保留原有真实限位、1.5rad目标偏差检查、传感器时效检查和显式 `--send`。来源运行时的 `GraspSkill` 另支持自动HOLD及外部显式HOLD；本目录没有新增硬件执行入口。
