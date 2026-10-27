# 四种可复用抓握接口：共同teacher混合DAgger/PPO蒸馏

## 用户确认的范围

以用户明确反馈真机表现良好的link-near mixed-PPO student训练流程为基础。四个独立Student：Cluster、Joint Pose、Fingertip、Hybrid。固定抓法目标在FORM/HOLD期间不变；指尖取同一个Sharpa q_seed的掌心系FK，而非MANO或物体坐标系。从2244条候选中使用同一个5200 teacher筛选真实执行成功案例，按原始parent分离训练/测试。

本轮先完成Experiment A / Setting 1：reference-derived commands。目标来自实际teacher成功执行的代表帧，不能称为Agent自主命令。Independent commands及冻结student后的Agent工具评测另行进行，不能混入本轮成功率。

## 四种模型

共同反馈每帧107维，历史8帧；GRU192、帧编码192、head128→22；相同动作scale/offset、外部腕部reference、真实手指限位、一次EMA控制。

| 接口 | 固定命令 | phase＋age | 总输入 |
|---|---|---|---|
| Cluster | 新link-near六类one-hot |3＋1|H8×117|
| Joint |22维q_seed，API单位rad；网络按原动作scale/offset归一化|3＋1|H8×133|
| Fingertip |5×3 Sharpa掌心系指尖，API单位m；网络除以0.1m|3＋1|H8×126|
| Hybrid |6维类别＋15维同一指尖目标|3＋1|H8×132|

本轮Hybrid使用完整五指尖，不引入额外mask或部分指尖命令。q_seed是条件，不覆盖关节动作；teacher仍读取原完整reference，不因student接口而改写teacher输入。

初始化统一使用原始28条C checkpoint的反馈、phase、GRU和head权重。把旧六类输入权重移除，新接口命令列全部清零；相同反馈/phase时四个模型初始输出相同。各模型第一层输入列数不同，隐藏层及后续容量不变。没有让Cluster直接保留已训练好的新类别权重而其他三组从零学命令。

## 数据和筛选

Teacher：`/mnt/cpfs/workspace/rq_ws/outputs/full_hoi_wrist_offset_20261026/train_contact_priority/model_5200.pt`。

候选为最终link-near六类均衡2244条。按448环境分批筛选，名义物理参数、真实关节限位、张手初态，EEF沿对应reference。

筛选要求：实际物体抬升≥2cm且至少两根手指与目标物体接触≥0.5N，连续0.5秒；reference结束后1秒HOLD至少95%帧维持上述状态。过20N比例和峰值另记录，不作为隐含额外筛选条件。这是在选择成功抓起并保持的数据，不涵盖所有“不需要抬升”的工具/桌面交互成功。

代表目标取首次确认成功抓起时的实际22关节角，指尖严格通过同一q的Sharpa FK生成。保留失败清单，统计每类成功与原始parent覆盖。通过后按parent约80/20划分；同一capture/原始parent的多个segment不能跨训练和测试。parent使用已有2244条selected清单，不靠文件名随机切段。保证有样本类别至少在训练出现，实际测试类别覆盖另报告。

留出仅指本轮student训练：5200 teacher及初始化控制主干可能已经见过这些数据，因此不是整个模型链条从未见过的新任务或新物体测试。测试目标从测试teacher执行提取，只属于Setting 1上界。

## 训练配方与保留项

- 从旧C初始化；student执行采样动作，teacher在实际访问状态在线提供动作标签。
- 300次update，每次32步，3epoch，batch上限4096；每条训练reference一个固定资产环境，四组相同数量。
- actor lr 3e-6，critic lr 3e-4，初始std .08；前5次只训练critic。
- loss：lambda×动作MSE＋(1−lambda)×PPO，另训练特权critic。lambda由0.9按200次更新退火到0.5。
- 不额外添加离线BC，不用beta混合teacher/student执行动作，不复用原28条纯DAgger消融的训练方式。
- 继承5200环境的DR、空间/腕部扰动配置及物体奖励，保留20N以上力惩罚、真实关节限位。
- 遵循原mixed pipeline的phase语义：前30步FORM对应张手监督；之后HOLD跟随teacher；RELEASE提供张手监督。该历史命名并非“FORM立即开始闭合”。运行时若Agent要从张手进入抓握，需要遵循此阶段语义。
- 新入口修复旧代码阶段age在切换时未准确归零的问题：直接从当前tick减本阶段起点得到age，四组一致，评测同样处理。其他阶段时序不变。不能称为旧程序逐行不变复现。
- 记录有效transition数，区分长短轨迹padding。各组相同最大epoch/更新预算；KL early-stop可能导致实际梯度步数不同，应报告实际值而非宣称完全相等。

## 评测与交付

训练集和parent留出集分别评测，固定同一外部EEF及初态；reference结束后保持5秒。输出抓起、1/5秒HOLD、掉落、异常力，另报固定目标的关节MAE和指尖误差。Cluster组也用同任务目标计算误差，但不把它读取了这些连续目标作为前提。

保存逐任务轨迹：实际手指/手腕、物体、物体过滤后的五指力、原始指尖力和phase，可继续做Contact Signature/Survival分析。连续目标只作为参考条件，不直接作为teacher奖励或物理成功标签。

本轮的四接口模型需用`InterfaceStudent`按checkpoint metadata加载。旧`run_link_near_cluster_student_live.sh`继续指向用户验证过的权重，不被自动替换；尤其Joint/Fingertip/Hybrid不能用旧H8×117 loader加载。真机反馈依然只属于此前link-near版本，新模型需评测后再部署验证。

## 代码与集群位置

- `interaction/interface_student.py`：网络、公共初始化、四种命令编码。
- `interaction/cluster_mixed_ppo.py`：复用原混合learner，按metadata选择新网络；旧checkpoint路径不变。
- `scripts/rsl_rl/screen_interface_teacher.py`：真实teacher筛选与固定目标采集。
- `scripts/prepare_interface_success_split.py`：成功数据与parent split。
- `scripts/rsl_rl/train_interface_mixed_ppo.py`：四接口共同训练入口。
- `scripts/rsl_rl/evaluate_interface_student.py`：共同物理和命令误差评测。
- `scripts/launch_interface_teacher_screen.sh` / `scripts/launch_interface_students.sh`：后台筛选及后续训练/评测。

远端目录：`/mnt/cpfs/workspace/rq_ws/outputs/interface_students_20261027`。

两项本地测试已通过：四接口初始化输出一致/编码维度正确；四种接口均能通过混合loss实际更新actor。当前集群在分批teacher筛选；训练进程等待完整筛选完成后生成共同split，再依次训练并评测四组。最终数据数量和效果尚未产生。

## 筛选完成与正式运行

2244条全部筛完，340条通过（340个原始parent）。272条训练、68条留出。

| 新类别 | 训练 | 测试 |
|---|---:|---:|
| C0 |11|1|
| C1 |25|6|
| C2 |89|21|
| C3 |18|5|
| C4 |3|4|
| C5 |126|31|

成功筛选后类别不再均衡，C0测试仅1个、C4总共7个，不能用小类别成功率给出强结论。四组使用完全相同的上述清单，既报告整体也报告逐类。划分结果已同步到本地`audit/interface_students_20261027/dataset/`。

两环境Joint真实仿真探针完成6次混合更新及评测；该探针只验证接口、FK命令一致性、梯度更新和模型恢复，不作为正式实验结果。初始化公平性复查后，保留已加载权重的网络构造不再消耗不同数量的全局随机数，避免输入宽度影响后续critic初始化。首个Cluster启动在仿真初始化阶段停止并作为`probe_cluster_initialization`保留，正式四组采用修正后的共同规则。

网络参数数：Cluster272534、Joint275606、Fingertip274262、Hybrid275414，最大差异约1.13%。

四组训练/评测完成后还会自动执行同一5200 teacher在训练/测试split、额外5秒HOLD下的配对评测，避免用筛选时1秒HOLD代替teacher的5秒表现。

固定目标来自代表帧，而teacher仍跟随完整时变reference，因此teacher本身也可能偏离这个静态目标。固定目标误差必须同时报告teacher数值，不能把全部偏差都解释为student不服从命令。

## 中途监督：Cluster完成、Joint接近完成

Cluster完成300次更新，耗时782.2秒（约13分钟），累计1191244个有效transition。Joint监督时为294/300，Fingertip与Hybrid尚待顺序运行，未发现后台报错。

Cluster原位闭环评测：训练272条中抓起142、1秒HOLD107、5秒HOLD91；留出68条中抓起39（57.4%）、1秒HOLD27（39.7%）、5秒HOLD24（35.3%）。留出固定目标指尖误差均值5.39cm、关节MAE0.412rad，统计于HOLD帧，不等于只对成功任务计算。连续目标并未作为Cluster输入；需要等其他接口及同协议teacher结果后再解释该误差。

这是本轮340条成功候选筛选后训练的新Cluster模型，不是用户已验证真机的原2244条link-near checkpoint。原真机默认模型未被这轮权重替换。局部汇总已同步`audit/interface_students_20261027/results/`。

更新：2026-10-27 02:23:38四接口训练、训练/留出评测与Teacher配对评测全部完成。[完整结果与权重位置](interface_students_results_20261027.md)。此前进度段落保留为历史快照。
