# 同场景手势替换：latent prior 与 seed-only student

配对任务 141 条；两版模型均使用相同物体、腕部轨迹、初态和由同一个机器人姿势生成的指尖目标/q_seed。

- latent nominal: 抓起 31/141；双指抬升 37/141；HOLD 指尖目标误差 3.4 cm；HOLD 关节目标 MAE 0.319 rad；>20 N 帧占比 0.156。
- latent swapped: 抓起 36/141；双指抬升 45/141；HOLD 指尖目标误差 3.6 cm；HOLD 关节目标 MAE 0.355 rad；>20 N 帧占比 0.147。
- latent：同任务更换手势后，关节 action target 的平均绝对变化 0.303 rad。
- seed nominal: 抓起 45/141；双指抬升 55/141；HOLD 指尖目标误差 2.4 cm；HOLD 关节目标 MAE 0.225 rad；>20 N 帧占比 0.102。
- seed swapped: 抓起 33/141；双指抬升 43/141；HOLD 指尖目标误差 2.6 cm；HOLD 关节目标 MAE 0.240 rad；>20 N 帧占比 0.138。
- seed：同任务更换手势后，关节 action target 的平均绝对变化 0.211 rad。

## 双来源 teacher 原任务都抓起的子集

这仅说明两个原任务可抓，不证明替换手势在目标腕部路径上可抓。

- latent nominal: 抓起 19/54；双指抬升 21/54；指尖误差 3.4 cm。
- latent swapped: 抓起 18/54；双指抬升 20/54；指尖误差 3.5 cm。
- seed nominal: 抓起 28/54；双指抬升 32/54；指尖误差 2.2 cm。
- seed swapped: 抓起 20/54；双指抬升 21/54；指尖误差 2.5 cm。

## 替换目标类别

- C1: 42 条；latent/seed 抓起 6/10；指尖误差 4.0/2.8 cm。
- C2: 25 条；latent/seed 抓起 8/7；指尖误差 2.9/2.6 cm。
- C3: 39 条；latent/seed 抓起 10/4；指尖误差 4.0/2.6 cm。
- C5: 35 条；latent/seed 抓起 12/12；指尖误差 3.3/2.3 cm。
