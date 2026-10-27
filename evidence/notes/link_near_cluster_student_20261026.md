# 最终 link-near cluster 的下一轮蒸馏

## 当前决定与状态

按用户2026-10-26指示，teacher续训完成后使用最终 `link_near_and_distance_joint` 六类及其2244条均衡清单。teacher训练及其采样权重没有因蒸馏修改。远端handoff已校验teacher最终checkpoint并自动完成mixed PPO；最终student已下载到本地audit目录。

Teacher来源：`/mnt/cpfs/workspace/rq_ws/outputs/full_hoi_wrist_offset_20261026/train_contact_priority`。训练计划终点5200；实际完成后读取真实checkpoint及对应params，不把未生成的5200当作已可用权重。

## 数据与标签

- 原始说明：[数据说明](../full_hoi_link_near_distance_balanced_dataset_20261026.md)。保留原CSV，不修改用户聚类结果。
- 全部2244条，六类各374条，2160个parent；parent不跨类。全部可按key匹配当前6244条teacher inventory。
- 对当前训练inventory按key重映射descriptor，确保继续使用当前训练资产和reference配置。CSV原路径同时保留在selected.json供追溯。
- 新cluster编号0–5是新的类别定义，不等同旧pose cluster或先前PhysX contact cluster。新student单独输出，不覆盖已部署C checkpoint；不直接继承旧六类命令的语义或旧seed。
- 原历史teacher联合成功数依次66/51/79/4/2/67，总269。这些指标不参与此次数据过滤，不作为新teacher标签。全部2244条保留，新的rollout结果独立记录。

## 沿用的student接口与蒸馏方式

本轮目标是混合DAgger/PPO蒸馏，损失按 `lambda * DAgger + (1-lambda) * PPO` 混合，并由student访问状态在线查询续训teacher。现有 `train_c0_dual_teacher_dagger.py` 只有多轮DAgger，不能直接宣称已实现这轮混合PPO；现有 `train_hand_goal_mixed_ppo.py` 的actor接口是连续关节/指尖goal，也不能直接接收新cluster命令。训练入口需要把混合损失、特权critic和在线teacher标签接到C系列8×117 GRU学生上。

沿用可部署C系列接口：8帧×117维，107维本体/掌心系速度/指尖力及有效性，加6维新cluster one-hot、3维FORM/HOLD/RELEASE和1维阶段持续时间。腕部外部控制；student不读取物体状态、绝对腕部位置或朝向。输出22维归一化手指动作，经原动作解码、平滑及真机限位得到关节目标。

复用现有DAgger流程：teacher保留训练时观测，在实际采样状态上产生动作监督，student读取上述局部历史；逐步降低teacher执行比例并积累student状态上的teacher标签。新cluster只标注student命令，不改写teacher参考手势。历史成功标签与几何近接标签均不充当teacher动作。

## 已准备的输入

目录：`audit/link_near_cluster_distill_20261026/inputs/`。

| 文件 | 用途 |
|---|---|
| references.json | 顺序对齐的2244个当前训练descriptor |
| cluster_ids.json | 新0–5命令编号 |
| teacher_map.json | 全部object，指向本轮续训teacher |
| selected.json | 原CSV字段、新编号和当前descriptor |
| summary.json | 数量、历史指标、teacher待完成状态 |

生成脚本：`scripts/prepare_link_near_cluster_distill.py`。输入为用户CSV及`audit/full_hoi_wrist_offset_20261026/reference_inventory.json`，输出上述目录。已检查2244个key唯一、每类374条及parent不跨类。

## Teacher完成后执行计划（已由下方执行记录更新）

1. 确认teacher训练终止、model_5200真实落盘并检查策略参数有限；当前训练仍在运行。蒸馏时teacher在student实际访问状态上在线提供动作标签。
2. 复用`scripts/rsl_rl/train_c0_dual_teacher_dagger.py`的student结构、命令编码和teacher查询，新增适配117维actor的mixed DAgger/PPO learner。critic读取仿真特权状态且不部署；采用明确的student on-policy状态、在线teacher标签、PPO回报。场景对每个环境固定实例化对应descriptor的物体USD，不能在reset时把某环境重指到不同物体。CSV含954种object_asset，因此采用2244环境、每条descriptor固定一个环境的全量并行方式，使六类都被覆盖且保持均衡。
3. 检查新teacher的wrist_offset与DR配置继承：旧入口会关闭部分control/object DR却继承其他stage字段，不能把这种隐式混合作为本轮明确配方。先做小批真实采集，明确记录teacher原观测、采集扰动和student传感器DR。
4. 使用新的cluster标签训练独立student；保留真机限位，验证FORM/HOLD/RELEASE、动作解码及命令切换。新六类没有已验证功能名称，不沿用旧C的固定抓法声明。
5. 同任务配对报告teacher/student表现，并单独展示C3/C4。全量候选保留；若发现失败监督造成明显问题，再以明确实验区分是否使用成功样本，不静默缩减用户清单。

CSV统计出954种资产；训练入口为每条参考固定对应环境，不通过改env_episode替换USD。mixed PPO rollout采用2244个并行环境覆盖全部候选。actor从已部署C0–C5学生初始化，但清零旧cluster输入层权重；PPO使用tanh-Gaussian动作分布，loss为`lambda*DAgger+(1-lambda)*PPO`，lambda由0.9降到0.5，critic读取特权状态。实际运行细节和结果见下方完成记录。任务级student评测仍待进行。

## 2026-10-26 teacher完成时的监督快照（历史）

用户确认本轮teacher完成后使用最终版 link-near-distance balanced cluster 数据。其来源为 `docs/full_hoi_link_near_distance_balanced_dataset_20261026.md` 与 `audit/functional_hand_object_clusters_20261025/full_train_hoi_6241/link_contact_clearance_comparison/balanced_selection/link_near_distance_balanced_hoi.csv`；manifold review 位于对应目录的 `manifold_review/index.html`。训练输入、cluster id 与 2244 条 descriptor 已按这份最终 CSV 准备并同步远端，六类各374条。

最近核查时，远端 teacher PID511459 正运行到3736/5200，日志 ETA 约7小时22分，最新checkpoint为model_3700.pt。handoff监督进程PID638269仍在等待；mixed PPO 尚未启动。远端GPU占用约58365/73415 MiB，利用率40%。teacher实际结束并通过最终权重检查后，监督脚本会自动启动mixed PPO；如果启动或Isaac初始化失败，需要根据日志修复并续跑。进程、日志和checkpoint以远端实时状态为准，本文记录仅作快照。

## 2026-10-26 mixed PPO 完成与交付

Teacher完成到5200；handoff脚本确认`model_5200.pt`有效后自动启动student。Student实际运行300/300 updates并写入`complete.json`，记录耗时996.3秒。训练配置为2244环境、每条reference固定一个环境、32步rollout、3个PPO epoch、4096 batch；lambda由0.9退火到0.5；force threshold 20N、真机关节限位开启。六类各374条。

远端最终checkpoint：`/mnt/cpfs/workspace/rq_ws/outputs/link_near_cluster_distill_20261026/mixed_ppo_v1/final/student.pt`。本地副本：[student_link_near_mixed_ppo.pt](../../audit/link_near_cluster_distill_20261026/student_link_near_mixed_ppo.pt)。本地还保存`metrics.jsonl`、`recipe.json`、`complete.json`及handoff状态。

Checkpoint在远端用PyTorch成功加载，22个关节名，10个student state tensors，权重有限；metadata记录新cluster方案和H8×117观测。训练诊断指标：平均object reward 0.4307（首轮0.5261、末轮0.4220），平均在线DAgger MSE 0.3921（末轮0.3084），平均tip force 0.0847 N，20N以上力惩罚均值0.000925，平均approximate KL 0.00497。`active_fraction`平均0.122、末轮0.00134，反映不同reference长度和同步episode tick下的有效transition比例；它不是成功率。尚无任务级rollout评测，因此这些训练指标不能证明抓取或保持能力。

handoff状态已更新为`completed`；训练进程已退出。后续如需判断这个student是否好用，应补做对应新cluster的FORM/HOLD/RELEASE任务级仿真评测，并与teacher做同任务对照。

本轮新增：

- `interaction/cluster_mixed_ppo.py`：8×117 C0CommandStudent的tanh-Gaussian PPO与在线DAgger混合learner，lambda按 `0.9→0.5` 退火；critic只读取仿真critic观测，部署不包含critic。
- `scripts/rsl_rl/train_link_near_cluster_mixed_ppo.py`：2244个环境和2244条descriptor一对一，使每种固定物体资产和六类均衡样本同时在场；teacher actor用完整训练观测，student actor仅读手/力/命令。object-only teacher reward用于PPO，另对超过20N的指尖力增加惩罚。保留真机关节限位和动作平滑。
- 初始化采用旧C0–C5的已部署学生，清零旧cluster输入权重，保留本体动作与phase表征，防止把旧标签语义误套到新簇。
- `scripts/run_link_near_cluster_mixed_ppo.sh`：正式训练入口，默认300次更新。
- `scripts/handoff_teacher_to_link_near_mixed_ppo.sh`：等待PID511459；检查最终5200迭代、权重有限和优化器状态，再自动启动student。

训练脚本及初始化checkpoint已同步远端并实际运行完成。自动接续脚本已退出；最终权重和训练指标留存在远端输出目录及本地audit目录。

06:05建立的`waiting_teacher`状态是历史记录；当前handoff状态已更新为`completed`，mixed PPO已完成300次更新。

## 2026-10-26 全量 student rollout 评测

使用最终 student checkpoint 对完整2244条 reference 做了确定性仿真 rollout，六类各374条，全部轨迹均产生有限指标。评测从张开手开始，腕部沿对应 HOI wrist reference 运动；FORM 时腕部暂停30步，随后执行 HOLD 并额外保持30步，最后执行 RELEASE 30步。student 使用训练时 H8×117 输入；评测关闭训练 DR、空间扰动和腕部 offset。该评测衡量 reference-conditioned rollout，不等价于任意物体抓取成功率或真机表现。

结果文件：[总体汇总](../../audit/link_near_cluster_distill_20261026/eval_student_full_20261026/summary.json)、[逐条episode](../../audit/link_near_cluster_distill_20261026/eval_student_full_20261026/episodes.jsonl)、[完成标记](../../audit/link_near_cluster_distill_20261026/eval_student_full_20261026/complete.json)。远端原始输出位于`/mnt/cpfs/workspace/rq_ws/outputs/link_near_cluster_distill_20261026/eval_student_full_20261026/`。

| 类别 | 条数 | 有≥2cm参考抬升 | 持续0.5s双指接触抬升（命中/有抬升目标） | HOLD帧位姿在3cm/30°内 | HOLD双指物体接触帧 | HOLD均值位置误差 | HOLD均值角度误差 | 末段保持通过* |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 | 374 | 250 | 94/250 (37.6%) | 16.2% | 31.2% | 22.0 cm | 61.1° | 5 |
| C1 | 374 | 282 | 66/282 (23.4%) | 23.4% | 27.3% | 9.9 cm | 45.1° | 16 |
| C2 | 374 | 352 | 86/352 (24.4%) | 23.2% | 27.1% | 29.5 cm | 52.9° | 10 |
| C3 | 374 | 344 | 37/344 (10.8%) | 16.8% | 9.5% | 27.3 cm | 68.1° | 1 |
| C4 | 374 | 44 | 7/44 (15.9%) | 79.9% | 4.4% | 2.8 cm | 14.5° | 0 |
| C5 | 374 | 373 | 72/373 (19.3%) | 26.3% | 19.7% | 14.3 cm | 51.0° | 3 |
| 总体 | 2244 | 1645 | 362/1645 (22.0%) | 31.0% | 19.8% | 17.6 cm | 48.8° | 35 |

按来源汇总的0.5s双指接触抬升：DexCanvas 169/487（34.7%）、DexterHand 0/5（样本很少）、quick HOI 30/241（12.4%）、Spider 163/912（17.9%）。分母只包括参考中物体抬升目标至少2cm的轨迹。总体实际最大抬升均值为5.1cm、中位数0.13cm；参考最大抬升均值为16.8cm。末段保持通过*要求最后30个HOLD帧中至少80%同时处于位置误差≤3cm、角度误差≤30°，且至少50%帧有两个物体接触手指。该定义是严格的跟踪和接触联合条件，不是单独的抓起判定。

初步结论：当前student能较干净地执行 RELEASE（无接触比例均值94.8%），但全量 HOLD/抬升能力还不够稳定：有明确抬升目标的1645条中，约21.6%达到“抬起至少2cm且持续双指接触0.5秒”；只有35/2244条满足末段保持联合条件。C1的平均追踪和末段保持相对较好，C0双指接触占比最高但位置/角度追踪误差较大。C4看起来追踪很好（位置2.8cm、角度14.5°），但它只有44条参考抬升≥2cm且双指接触帧仅4.4%，所以主要反映其参考物体运动幅度较小，不能解释为抓取效果好。C3最弱，HOLD双指接触仅9.5%，末段保持通过1条。

因此这轮评测还不能支持“可泛化功能性抓取”结论。下一步应先浏览成功与失败 episode 配对，重点看C3、C5和Spider/quick HOI失败是否来自命令条件、手指接触建立、teacher/reference本身可执行性或评测启动时序；再针对找到的失效机制做小范围修正和同协议复测。不要仅凭混合PPO训练reward判断抓取能力。

## 2026-10-27 用户真机反馈

用户明确确认：`bash scripts/run_link_near_cluster_student_live.sh --send` 对应的student在真机上表现良好。此为用户实际测试反馈，不是离线推理或仿真结果。

启动器默认权重为 `audit/link_near_cluster_distill_20261026/student_link_near_mixed_ppo.pt`（未通过 `LINK_NEAR_STUDENT_CHECKPOINT` 或 `--checkpoint` 覆盖时）。对应新版link-near六类、2244条均衡HOI，teacher为腕部offset/空间课程续训后的object-goal model_5200；从旧C student初始化并清零旧类别输入权重，执行300次混合DAgger/PPO更新，lambda从0.9降至0.5。

记录状态：**用户报告真机表现良好**。测试物体、类别、次数、保持时长及腕部运动范围尚未记录，不据此补写量化成功率。该反馈应归属此link-near mixed-PPO版本，而不是原始28条纯DAgger C版本或其31条纯PPO续训版。既有全量reference仿真评测结果保留，两者任务条件不同，不能互相替代。
