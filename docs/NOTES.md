# 论文与复现要点

PDF 均来自 arXiv 官方,编号与标题已用 arXiv API 核对(2026-09-29)。
下面只记**已读原文核实过**的复现相关信息;标"未读"的还没核对,不要引用。

| 文件 | 论文 | 状态 |
|---|---|---|
| `ACT_2304.13705v1.pdf` | Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware | 未读 |
| `DiffusionPolicy_2303.04137v5.pdf` | Diffusion Policy: Visuomotor Policy Learning via Action Diffusion | 未读 |
| `OpenVLA_2406.09246v3.pdf` | OpenVLA: An Open-Source Vision-Language-Action Model | 未读(基准取自官方 README) |
| `LIBERO_2306.03310v2.pdf` | LIBERO: Benchmarking Knowledge Transfer for Lifelong Robot Learning | 未读 |
| `SmolVLA_2506.01844v1.pdf` | SmolVLA: A Vision-Language-Action Model for Affordable and Efficient Robotics | **已读仿真部分** |
| `pi0_2410.24164v4.pdf` | π0: A Vision-Language-Action Flow Model for General Robot Control | 未读 |
| `pi05_2504.16054v1.pdf` | π0.5: a Vision-Language-Action Model with Open-World Generalization | 未读 |

## ACT(已复现)

- 基准来源:不是论文,是 HF 仓库 `lerobot/act_aloha_sim_transfer_cube_human@ba73b276` 自带的 `eval_info.json`:Transfer Cube 成功率 **83.0%**(500 回合)。
- 本机:**83.2%**(500 回合,seed 1000)。

## OpenVLA(已复现)

- 本机:**86.2%**(431/500,seed 7,单种子 95% CI ±3.0),各任务 72–98%。与基准 84.7 ± 0.9% 一致。

- 来源:openvla 官方 README @ `c8f03f48`(论文 v2 附录 E 的结果照抄在 README 里)。
- LIBERO-Spatial **84.7 ± 0.9%**,3 个种子 × 500 回合(10 任务 × 50 次),A100。
- 版本必须是:Python 3.10.13、PyTorch 2.2.0、transformers 4.40.1、flash-attn 2.5.5;评测加 `--center_crop True`(训练用了 90% 面积随机裁剪)。
- MuJoCo ≥ 3.3.3 会让 LIBERO 渲染变暗,需用 3.3.2(LIBERO issue #88,OpenVLA 一作;openvla issue #282 有人因此从 ~70% 掉到 62.6%,降级后回到 85%)。

## SmolVLA(未复现到论文数字)

- 本机 `HuggingFaceVLA/smolvla_libero`:**75.2%**(500 回合,batch_size=10);按论文协议取每任务前 10 次为 72%。
- 社区用同一权重的实测(lerobot issue #2354):Spatial 82–83%。reobf 指出该权重 `expert_width_multiplier=0.5`、VLM 32 层,
  论文是 0.75、16 层,且权重疑似欠拟合 —— **公开权重本身达不到论文的 90%**。
- 本机比社区再低约 7 个百分点,待排查:~~batch_size=10~~(对照 A:batch_size=1 得 75.0%/100 回合,**已排除**)、`n_action_steps=10`(对照 B,进行中)。
- 已排除:`max_parallel_tasks=1`(issue #4341 的共享策略状态 bug 不适用);fps=20;mujoco 3.3.2(issue #4390 是 ≥3.4.0 的问题)。

出处:论文 Table 2 及正文实验设置。

- LIBERO 成功率(SmolVLA 0.45B,无机器人数据预训练):Spatial **90** / Object 96 / Goal 92 / Long 71 / 平均 87.3。
- 同表对照:π0(3.3B,有预训练)Spatial 90 / Object 86 / Goal 95 / Long 73 / 平均 86.0;OpenVLA 84.7 / 88.4 / 79.2 / 53.7。
- **评测协议:每个任务 10 次,每个套件 100 回合**。因此 90% 本身的 95% 置信区间约 ±6 个百分点。
- 训练:数据集 `physical-intelligence/libero`(1,693 条),4 个套件多任务训练;100k 步,batch 64。
- **`n_action_steps` 影响很大**(Table 13,四个套件的平均值):1 步 80.3 / 10 步 82.8 / 30 步 70.8 / 50 步 51.8。
  Table 12 的 chunk 大小:10 → 84.0,50 → 80.3。
- 两个公开权重的对照(配置读自 HF):
  - `HuggingFaceVLA/smolvla_libero@6721902b`:`n_action_steps=1`,输入键 `image`/`image2`(对应 physical-intelligence/libero 的命名)。**最接近论文,作为主复现对象。**
    但 `num_vlm_layers=0`:按 LeRobot 代码(`smolvlm_with_expert.py:102`)只有 >0 才截断,即**用了 SmolVLM2-500M 的全部层**,
    而论文主模型只用前一半(N=16,Table 8)。权重 1218MB,比 16 层的 `lerobot` 版(907MB)大,与此一致。对照论文数字时要记住这点。
  - `lerobot/smolvla_libero@31d453f7`:`n_action_steps=50`,只在 `libero_spatial` 上训练,25k 步、batch 32。与论文设置不同,只作对照。

## π0.5(已复现)

- 权重 `lerobot/pi05_libero_finetuned_v044@8e174154`(safetensors,不受限);分词器来自受限仓库 `google/paligemma-3b-pt-224`,本地副本。
- 评测按 LeRobot `docs/source/libero.mdx` 加 `--policy.n_action_steps=10`(文档称与 OpenPI 一致)。
- 本机:**98.0%**(500 回合,95% CI ±1.2);基准 LeRobot 97.0%(每任务 10 次)、OpenPI 98.8%。

## Diffusion Policy(已复现,PushT)

- 原计划 robomimic(MuJoCo)因官方老环境(Python 3.9 / torch 1.12 / mujoco-py 2.1 / gym 0.21)超出限时,按约定止损改 PushT(2D 物理,非 MuJoCo)。
- 权重 `lerobot/diffusion_pusht@84a7c231`(旧格式,本地迁移;迁移脚本遇 list→tuple 编码 bug,用不改源码的包装脚本绕过)。
- 本机:**63.0%**(500 回合,±4.2),avg_max_reward 0.941;基准 LeRobot 模型卡 65.4%,原版 DP 仓库同等模型 64.2%。

## π0(未复现到论文数字)

- 权重 `lerobot/pi0_libero_finetuned_v044@45dcc8fc`;评测 `--policy.n_action_steps=5`,对齐 OpenPI 基准所用脚本 `examples/libero/main.py@c015073f` 的 `replan_steps=5`。
- 基准:OpenPI LIBERO README 旧版(commit c015073f)π0 @30k 微调 Spatial **96.8%**。注意这是 OpenPI 自己训练的权重,不是 LeRobot 这个。
- 本机:**73.4%**(500 回合,±3.9);各任务 68/86/92/84/58/64/78/80/68/56。
- 社区同一 LeRobot 权重(lerobot issue #2114):Spatial 69%(mujoco 2.3.7)→ **73%**(mujoco 3.3.2),与本机一致。
- LeRobot 维护者 pkooij(#2114,2025-10-05):"The Pi0 checkpoint is finetuned but needs more training to achieve results similar to the paper." —— **公开权重训练不足**。
- 旁证 #3591:把两路相机全涂黑,该 π0 仍有约 60%(正常 74.6%),疑似很少依赖视觉(LIBERO 场景变化小,可能靠语言 + 本体状态"背答案")。未在本机验证。

## 实验 B:视觉依赖测试(本项目自做,2026-09-30)

- 方法:包装脚本把送进策略的相机画面换成全黑(LeRobot 系替换 `lerobot_eval.preprocess_observation`;OpenVLA 替换 `get_libero_image`),不改任何源码;
  录像仍是真实渲染。每模型 LIBERO-Spatial 10 任务 × 10 次;对照组取各自 500 回合评测里每任务前 10 次(同种子、同初始状态)。
- 结果(正常 → 全黑):π0.5 99 → 0,OpenVLA 81 → 0,SmolVLA 72 → 0,**π0 76 → 56**。
- π0 全黑时各任务:7 8 9 8 6 **1** 9 **0** 7 **1** —— 只有"碗在小烤碗上 / 灶台上 / 木柜顶上"三个任务失败。
- 与 lerobot issue #3591(全黑约 60%)一致,本机独立复现。解读(待验证):该 π0 权重大量依赖语言 + 本体状态"背轨迹",
  这也可能是它达不到论文水平的原因之一。
- 实验 A(同期):π0 的 `n_action_steps` 5 / 10 / 50 → 76 / 70 / 68%(各 100 回合),差异在误差内,设置不是主因。

### 实验 b:π0 是否"背轨迹"(视频逐帧比较,CPU)

- 同任务同回合编号(同初始状态)的录像,缩到 90×90 灰度按时间步对齐,逐帧平均绝对差。自检:第 0 帧差异 0.35/255,回合对齐无误。
- 全程平均差异:π0 涂黑 vs π0 正常 **6.05**;对照 π0.5 正常 vs π0 正常 **5.22**。涂黑后仍成功的回合 5.35,失败的 6.93。
- 结论:**"完整重放同一条轨迹"不成立** —— 看不见时 π0 的动作与看得见时的差别,不比两个不同模型之间的差别小。
  更可能是按任务描述执行一套"平均解法";LIBERO 物体位置扰动小,多数任务够用,碗位置特殊的 3 个任务(5/7/9)失效(差异 7.7–8.3 vs 对照 ~5)。
- 更正(2026-09-30):上一条的"平均解法"猜测被方向 1 的末端轨迹数据否定(抓取点并未聚拢),结论以方向 1 为准。
- 局限:像素差按时间对齐,无法区分"路线不同"与"快慢不同"。确定性结论需记录末端执行器轨迹(需 GPU 重跑)。

### 方向 1:末端执行器轨迹(2026-09-30,每组 100 回合,同种子同初始状态)

- 包装脚本 `eval_probe.py` 逐步记录 `robot_state.eef.pos` 与夹爪开合;DTW 消除快慢差异只比路线;抓取点 = 夹爪首次明显合拢时的末端位置。
- 路线 DTW / 抓取点距离:噪声底线(π0 正常跑两次)**2.12 / 1.51 cm**;π0 全涂黑 vs 正常 **4.44 / 5.03 cm**;π0.5 vs π0(都正常)3.28 / 2.65 cm。
- 同任务 10 回合抓取点离散度:π0 正常 1.78、重跑 1.79、全涂黑 2.41(去掉任务 7 约 1.9)、π0.5 1.56 cm。
- 结论:看不见时 π0 走的是另一条路线(差异为噪声的 2 倍),但抓取点并未"聚成一团" —— "平均解法"的猜测也不成立。
  更可能是 **LIBERO-Spatial 场景变化本身很小**(同任务抓取点离散约 1.8 cm,与同一模型两次运行的噪声 1.5 cm 同量级),
  碗宽十余厘米,抓偏约 5 cm 仍有约一半机会成功。
- 注意:其余三个模型全涂黑降到 0%,不一定说明它们"用视觉定位";全黑图是训练分布外输入,也可能直接扰乱动作输出。
  需用加噪声 / 换场景画面等温和扰动区分。

### 方向 2:只涂黑一路相机(2026-10-01,每组 100 回合;image = 主视角 agentview,image2 = 腕部 eye_in_hand)

| 模型 | 正常 | 只涂主视角 | 只涂腕部 | 全涂黑 |
|---|---|---|---|---|
| π0 | 76 | **78** | 59 | 56 |
| π0.5 | 99 | 51 | **0** | 0 |
| SmolVLA | 72 | 2 | 5 | 0 |

- π0:主视角涂黑**毫无影响**,只靠腕部相机;腕部涂黑后的 59% 与全涂黑 56% 相当 —— 主视角对它几乎没有贡献。
- π0.5:**离不开腕部相机**(涂腕部即 0%),主视角涂黑降到 51%,两路都在用,腕部更关键。
- SmolVLA:任一路涂黑都几乎归零(2% / 5%)。这更像是对"训练分布外输入"极其敏感,而不一定是两路都在做定位(见方向 1 的注意事项)。

### 方向 3:继续微调 π0,训练时随机置零状态输入(2026-10-01)

- 设置:从 `lerobot/pi0_libero_finetuned_v044` 继续训练,数据 `lerobot/libero@a1aaacb7`;`train_expert_only`(冻结 VLM,只训动作专家)、
  bf16、梯度检查点、batch 16、3000 步(每组约 3.5 小时,显存峰值 15.5GB)。训练量约为原训练(1 万步 × batch 32)的 15%。
- 两组:对照 `STATE_DROP_P=0`;改动组 `STATE_DROP_P=0.5`(按样本把已归一化的 `observation.state` 置零,只在训练时)。
- 训练损失:对照 0.145 → 0.135(本已收敛);改动组首批 **0.835**(去掉状态后损失跳到约 6 倍 —— 原 π0 强烈依赖状态输入)→ 0.264。
- 评测(LIBERO-Spatial,每项 100 回合,n_action_steps=5):

| 模型 | 正常 | 全涂黑 | 下降 |
|---|---|---|---|
| 原始 π0 | 76 | 56 | 20 |
| 继续微调·对照 | 78 | 61 | 17 |
| 继续微调·状态置零 | 68 | **40** | **28** |

- 全涂黑:改动组 40% vs 对照 61%,差 21 个百分点,z≈3.0(两比例检验,p≈0.003)—— **改动显著降低了"不看画面也能做"的能力,即更依赖视觉**。
- 正常:改动组 68% vs 对照 78%,差 10 个百分点,z≈1.6(p≈0.11)—— 有下降趋势但不显著。
- 结论:状态置零能把 π0 推向更依赖视觉,但在这个训练量下没有带来整体成功率的提升。训练量仅为原训练的 15%,
  改动组损失仍未降到对照水平,更长的训练是否能在"更依赖视觉"的同时追回成功率,是下一步的问题。

### 温和扰动:加噪声 / 冻结画面(2026-10-01,每组 100 回合,同种子同初始状态)

- 动机:全黑图是训练分布外输入,三个模型降到 0% 不一定说明它们"用视觉定位",也可能只是被分布外输入扰乱。用两种更温和的扰动区分:
  加高斯噪声(标准差 0.1,画面内容还在)、冻结首帧(真实、分布内的画面,但整个回合不更新)。
- 结果(成功次数 / 100,正常 → 加噪声 → 冻结首帧 → 全涂黑):π0 76 → 79 → 71 → 56;π0.5 99 → 99 → 0 → 0;SmolVLA 72 → 32 → (在跑) → 0。
- 结论:π0.5 对噪声不敏感,但画面一冻结就归零 —— 它确实在闭环地用实时画面,全涂黑降到 0% 不是分布外输入造成的假象。
  π0 冻结首帧只掉 5 个百分点(在误差内),说明它基本不需要实时视觉反馈。SmolVLA 连轻微噪声都承受不住,支持"对分布外输入敏感"的解释。
