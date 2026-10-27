# 灵巧手 policy 接口、蒸馏与手姿 Manifold：阶段性实验结论

日期：2026-10-27  
范围：Sharpa 右手 System0/teacher/student、HOI 与 Sharpa 手姿表示、Agent-facing grasp interface。本文汇总已完成的对照和数据分析；探索中的解释单独标出，不把单次实验外推为普遍规律。

## 摘要

目前的证据支持三点。

1. **有结构的姿态库能改善关节空间覆盖，但几何覆盖并不等同于功能抓握。** 在限位内姿态集合上，KMeans/PCA-KMeans Pose Bank 的最近姿态误差优于同规模随机库；而接触类别消融没有证明姿态类别能稳定组织成功抓握的接触模式。
2. **更丰富的命令接口尚未在闭环任务成功率上显示稳定优势。** 在共同数据、teacher、传感反馈和近似训练预算下，Hybrid 的留出抓起率最高，Joint 的 5 秒保持最高，但差异不大，且四种 Student 均明显落后于 Teacher。
3. **Manifold-guided 选样尚未证明优于配额匹配随机选样。** 扩大到 2,365 条配对评测后，guided 与 random 抓起保持率几乎相同；现有结果不足以支持该选样策略带来总体抓取收益。

这些结果共同提示：姿态表示和类别命令可作为可用的接口组织方式，但不能替代对真实闭环接触建立、保持、命令跟随和目标任务成功的评测。

## 1. Agent 控制策略的边界

当前较清楚的系统分工是：Agent 低频选择抓握意图与阶段，student 高频闭环控制手指，腕部/机械臂由外部控制器执行。现有 grasp skill 以 `set_grasp`、`execute_phase(FORM/HOLD/RELEASE)`、`get_status` 暴露命令；部署时按控制频率维护历史输入和阶段时长。

student 的手部反馈可以包含本体状态、局部速度、掌心系指尖力/有效位和命令历史；它不应被默认描述为读取物体真值或未来参考。Teacher 可以在训练中读取更丰富的手物状态及 reference，再为 student 实际访问到的状态提供动作监督。

`q_seed` / pose command 是手型条件或建议，不应被解释为必须逐帧锁定的关节轨迹。腕部路径、空间定位和手指技能是当前接口中的不同职责。类别编号也只表示具体数据方案中的一个分组；旧 C0–C5、PhysX contact cluster 与最终 link-near cluster 不是可互换的语义标签。

**范围限制：** 用户反馈 `run_link_near_cluster_student_live.sh --send` 对应 student 真机表现良好，但没有记录物体、抓握类别、次数、保持时长和腕部运动范围，故属于重要的定性真机反馈，不是量化通过率。与之同时，link-near mixed-PPO student 在 2,244 条 HOI reference rollout 上的统一仿真表现较弱；两种设置任务条件不同，应并列保留，不能互相抵消或替代。

## 2. 四种 command interface 的受控蒸馏

### 实验设置

四组独立 student 分别接收 Cluster、Joint Pose、Fingertip、Hybrid 命令。共同设置包括：同一个 5200 teacher、同一批 teacher 实际执行成功抓起并末尾保持的参考、H8×107 手部反馈、GRU 主体、22 维动作、控制器、DR、奖励和外部腕部参考。Joint/Fingertip/Hybrid 的固定手型命令在 FORM/HOLD 中保持不变；指尖目标由同一个 Sharpa `q_seed` 经 FK 计算，保证 Joint 与 Fingertip 表达的是同一目标手型。

从 2,244 条候选中筛得 340 条符合筛选条件的 teacher rollout，按原始 parent 分成 272 条训练与 68 条留出。各组训练 300 次更新，模型参数量约 27.3 万；KL early-stop 导致实际优化步数略有差别。Student 使用共同初始化的反馈/GRU/phase 权重，命令输入列清零。

### 留出集结果

| 模型 | 抓起 | HOLD 1 秒 | HOLD 5 秒 | 抓起后掉落 |
|---|---:|---:|---:|---:|
| Teacher | 64/68 (94.1%) | 60/68 (88.2%) | 54/68 (79.4%) | 7/64 |
| Cluster | 39/68 (57.4%) | 27/68 (39.7%) | 24/68 (35.3%) | 14/39 |
| Joint | 34/68 (50.0%) | 27/68 (39.7%) | 26/68 (38.2%) | 5/34 |
| Fingertip | 35/68 (51.5%) | 24/68 (35.3%) | 22/68 (32.4%) | 12/35 |
| Hybrid | 41/68 (60.3%) | 31/68 (45.6%) | 25/68 (36.8%) | 11/41 |

固定目标符合度的留出 HOLD 帧平均误差也没有显示连续命令天然带来更准的跟随：Cluster/Joint/Fingertip/Hybrid 的关节 MAE 分别为 0.412/0.404/0.417/0.402 rad，指尖误差为 5.39/5.47/5.55/5.30 cm。

### 可以得出的结论

- 本实验内 Hybrid 抓起数最高，Joint 的 5 秒 HOLD 数最高；没有一个接口在所有任务指标上占优。
- 四个 student 的抓起率约为 50–60%，明显低于 teacher 的 94%。差距在训练集也存在，因此目前不能把瓶颈简化为 parent 留出泛化。
- Joint pose 和 fingertip command 比 cluster 携带更明确的目标量，但当前配方没有把这种额外信息转化成明显更低的目标误差或更高的任务成功率。
- 当前数据是 reference-derived command 设置：目标从 teacher 执行轨迹提取。这测量的是给定一个可行参考命令时的 student 学习能力，不是 LLM 独立选姿或生成目标的能力。

**尚不能得出的结论：** 68 条留出、单个训练 seed 不足以对接口排名；没有完成 independent-command 或 LLM Agent 端到端对比；teacher 主干可能接触过本轮留出轨迹；这批实验模型不是用户报告真机表现良好的原 link-near mixed-PPO 模型。

## 3. Manifold-guided 示范选择

扩大评测使用相同 2,365 条 HOI 任务、相同 teacher、固定的 Random/Guided Student checkpoint 与同一物理执行协议；每个 student 使用 30 条示范、60,000 次 teacher 查询和 400 次训练更新。训练 reference parent 被排除在评测之外。

| 评测集合 | Teacher | Random | Guided | Guided − Random |
|---|---:|---:|---:|---:|
| 全部 2,365 条 | 560/2365 (23.7%) | 354/2365 (15.0%) | 343/2365 (14.5%) | −0.47 pp |
| 历史抓起＋pose成功 521 条 | 147/521 (28.2%) | 106/521 (20.3%) | 100/521 (19.2%) | −1.15 pp |
| 参考抬升至少 2 cm 的 2,060 条 | 553/2060 (26.8%) | 348/2060 (16.9%) | 335/2060 (16.3%) | −0.63 pp |

按 parent 配对 bootstrap 的总体差异 95% 区间为 −2.13 至 +1.19 个百分点，跨越零。严格抓起加末段 pose 联合成功为 Teacher 89 条、Random 32 条、Guided 14 条。旧 14 条小测试中 guided 曾为 7/14、random 为 5/14，但这一差异没有在扩大评测中保持。

**结论：** 当前 Manifold-guided 选样和训练预算没有显示总体任务成功率优势。小样本观察不能作为方法成功证据；当前结果也不证明两种选样等效。类别上的变化方向不一致，下一轮更应检查入选动作的闭合时序、接触建立过程和 teacher rollout 质量，而不是只增加静态几何覆盖。

## 4. 手姿 Pose Bank：覆盖收益与功能边界

对限位内 Sharpa 右手 22D 姿态的 source-balanced 分析显示：

- 同规模 KMeans/PCA-KMeans bank 的最近姿态关节误差优于随机 bank。来源宏平均中位误差在 K=6 时为 0.276 rad（最佳聚类）对 0.324 rad（随机）；K=24 时为 0.226 对 0.260 rad；K=192 时为 0.181 对 0.199 rad。
- Joint KMeans 与 PCA-KMeans 的覆盖非常接近。例如 K=24 时分别为 0.2263 和 0.2264 rad；没有证据表明先降维是构建覆盖良好 bank 的必要条件。
- 解释方差不能代替执行精度。PCA-14 保留 96.1% 方差，但裁剪限位后五指指尖 FK 误差仍均值 10.1 mm、P95 26.7 mm；低维重建在裁剪前有较高关节越界比例。
- 该分析是关节几何覆盖，不包括 PhysX 自碰撞验证、真实接触稳定性或抓取成功标签。几何近邻和多样性都不能单独证明一个 pose 可执行或有功能语义。

另一次实际 rollout 的五指二值接触 signature 分析中，姿态类别 E2 没有显示清晰的类内接触一致、类间接触分离；随机固定分组 E1 在该批中的数值更高，但只有一次随机划分/单个训练 seed，且五指二值接触信息有限。因此结果不能解释为随机标签有语义，也不能据此否定姿态 manifold。

## 5. Contact 稳定性应与 grasp success 分开报告

接触分析已经区分真实执行接触与 reference 手型：以实际 PhysX 的目标物体过滤接触为主，按首次持续 0.5 秒的多指接触抬升对齐抓起时刻。未抓起任务不混入“抓起后保持”生存曲线；HOLD 接触中断、接触手指数、受力变异和首次失稳时间单独记录。

在共同成功 case 上，随机分组 E1 的 5 秒条件 survival 为 80.0%，姿态类 E2 为 74.7%，Teacher 为 69.5%，无类别 E0 为 62.2%。E1 同时有更少接触中断和较低的有效接触力变异，但这些是同一批实验里的相关性观察，不是随机分组本身提高稳定性的因果证据。

分析保存的信号不包含逐 link 接触、接触位置与物体局部接触法向，因而不应伪造对向力闭合或精细接触拓扑。建议正式 benchmark 同时报告：

1. 抓起建立率；
2. 抓起后的条件 survival/掉落；
3. 固定公共时间窗内的无条件成功保持率；
4. 接触中断、有效接触手指数及力统计；
5. 严格物体目标跟踪或放置成功。

## 6. 数据和结果的解释规范

- **数据有标注**不等于**本任务要求策略满足该字段**。reference 可同时含关节、指尖、物体和接触信息；训练命令需明确哪些数据用于监督，哪些约束实际输入策略。
- **缺少接触标签不表示禁止接触；没有力目标不表示目标力为零。** 抓握成功依赖真实 rollout 的物理结果，不能仅以 reference 姿态看似合理代替。
- **成功筛选有任务定义边界。** 本报告的抓起筛选包括物体抬升≥2 cm 与至少两指接触持续条件，不覆盖所有桌面功能交互或不要求抬升的任务。
- **留出粒度影响结论。** 以 parent/capture 为组留出可减少同源 segment 泄漏；但如果 teacher 或共同预训练主干用过这些轨迹，不能称为整个模型链条的严格 unseen 数据。
- **跨模态命令要分别测试 grounding。** Reference-derived command 是可行命令上界；从 Pose Bank、人手姿态或 RGB-D 独立构造命令属于另一实验，不应混用成功率。
- **sim、runtime 和硬件证据分开。** API 算术一致、仿真闭环成功、用户真机体验和有重复统计的硬件通过率是不同级别的证据。

## 7. 下一步研究优先级

1. 对四接口 student 做逐任务失败归因：命令敏感性、FORM 时序、teacher/student 访问状态差异、物体接触建立和长时 HOLD 分开看。
2. 固定一套可复用的 held-out 场景，扩展训练 seed 或重复 rollout，再比较接口和 Manifold 选样；保留类别及来源分层统计。
3. 单独进行 Independent-command 测试，让 Agent/pose selector 在训练样本以外生成命令；报告合法率、物理可行率、Student 条件执行率和端到端成功率。
4. 将 Pose Bank 候选经过关节限位、FK 误差与 PhysX 碰撞/接触检查后，再进入可调用 grasp skill；工具描述只声明经过评测的资产/几何范围。
5. 若要改善 student 与 teacher 的差距，优先用 student rollout 上的真实闭环错误诊断及在线 teacher action label 验证 DAgger/混合 PPO 的作用；不要仅凭训练 loss、reference 跟踪误差或 seed 可视化声称可部署。

## 8. 证据来源

下列来源属于 dexhand_hoi_learning 项目；这里摘录关键指标以便技术报告独立阅读，原始配置、逐条 episode 与分析细节以来源文档为准。

- 四接口实验设置：[interface_students_20261027.md](/home/ruoqu/crq_ws/dexx/dexhand_hoi_learning/docs/distill/interface_students_20261027.md)
- 四接口首轮结果：[interface_students_results_20261027.md](/home/ruoqu/crq_ws/dexx/dexhand_hoi_learning/docs/distill/interface_students_results_20261027.md)
- 扩大 Manifold-guided 评测：[manifold_guided_expanded_eval_20261026.md](/home/ruoqu/crq_ws/dexx/dexhand_hoi_learning/docs/distill/manifold_guided_expanded_eval_20261026.md)
- Contact Signature 与 survival：[command_ablation_contact_analysis_20261027.md](/home/ruoqu/crq_ws/dexx/dexhand_hoi_learning/docs/distill/command_ablation_contact_analysis_20261027.md)
- Pose Manifold E1 数据与指标：[pose_manifold_e1_20261027.md](/home/ruoqu/crq_ws/dexx/dexhand_hoi_learning/docs/pose_manifold_e1_20261027.md)
- link-near mixed-PPO Student rollout：[link_near_cluster_student_20261026.md](/home/ruoqu/crq_ws/dexx/dexhand_hoi_learning/docs/distill/link_near_cluster_student_20261026.md)
- 当前 Grasp Harness 项目边界：[PROJECT.md](../docs/current/PROJECT.md)
- 完整 HOI/Pose Manifold 图表与媒体：[POSE_HOI_REPORT.md](POSE_HOI_REPORT.md)
