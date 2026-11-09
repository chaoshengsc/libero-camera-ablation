const R = Array.isArray(window.RESULTS) ? window.RESULTS : [];
const $ = (id) => document.getElementById(id);
const fmt = (x) => x == null ? "—" : x.toFixed(1) + "%";
const sum = (a) => a.reduce((p, q) => p + q, 0);

// ---- 语言：默认跟随浏览器，？lang=zh|en 或右上角按钮切换。英文版在渲染后按词典替换文本（整句在前，短词在后）。
const LANG = new URLSearchParams(location.search).get("lang") || ((navigator.language || "").toLowerCase().startsWith("zh") ? "zh" : "en");
const DICT = [
  ["全黑对照：LeRobot π0 v044全黑成功率", "All-black comparison: LeRobot π0 v044 success"],
  ["其他所测检查点为0%：", "Other tested checkpoints score 0%: "],
  ["腕部单因素实验：π0.5屏蔽腕部后的成功率", "Wrist-camera study: π0.5 success with wrist masking"],
  ["只冻结腕部为", "Wrist-only freezing scores"],
  ["%；每条件", "%; per condition: "],
  ["回合", " episodes"],
  ["腕部单因素实验数据尚未加载", "Wrist-study data could not be loaded"],
  ["可直接核对下方结果与CSV", "Results and CSVs remain available below"],
  ["相机槽位修复：6个策略、27项回归用例", "Camera-slot fix: six policies, 27 regression cases"],
  ["提交前：旧21失败／6通过 → 修后27/27通过", "Before submission: old 21 failed/6 passed → fixed 27/27 passed"],

  ["本项目使用公开检查点，在LIBERO-Spatial中评测π0、π0.5、OpenVLA和SmolVLA在相机干预下的任务表现。实验包括四模型全黑对照、三个双视角模型的扰动对照，以及π0／π0.5的腕部单因素实验。", "This project evaluates public checkpoints of π0, π0.5, OpenVLA and SmolVLA under camera interventions in LIBERO-Spatial. It includes four-policy all-black comparisons, perturbation tests on three dual-view policies, and wrist-camera tests on π0/π0.5."],
  ["固定动作在选择外状态上保留成功表现", "Fixed actions retain successes on selection-excluded states"],
  ["腕部图显示各条件Wilson区间，配对差使用正态近似；官方π0图逐次展示匹配100初态结果；P1/P2的bootstrap方法分别注明。", "Wrist bars show per-condition Wilson intervals; paired differences use a normal approximation. The official π0 figure shows matched 100 runs separately. P1/P2 document their respective bootstrap methods."],
  ["评测协议与输入结构保留完整说明", "Evaluation protocols and input structure remain fully documented"],
  ["π0.5屏蔽腕部后从98.4%降到4.6%；同样的腕部干预没有使π0 v044出现相同降幅。", "π0.5 falls from 98.4% to 4.6% with wrist masking; π0 v044 does not show the same decrease."],
  ["实际任务示例是拿起盘子与小烤碗之间的黑碗并放到盘子上。主视角看场景，腕部相机看手边；π0／π0.5还接收机械臂状态与任务指令。", "One recorded task moves the black bowl between the plate and ramekin onto the plate. The agent view shows the scene, the wrist view shows the hand workspace; π0/π0.5 also receive state and instruction."],
  ["π0与π0.5的观测与动作形成闭环", "π0 and π0.5 observations and actions form a closed loop"],
  ["黑图保留视觉掩码；屏蔽在原槽位将掩码置0；冻结持续使用真实腕部首帧。主视角与状态正常更新。正常、腕部mask和腕部冻结的新运行条件各10任务×50初态；π0.5腕部黑图仍为历史5×100。", "Black images retain their visual mask; masking disables the original slot; freezing repeats the real first wrist frame. Agent view and state update live. New normal/wrist-mask/wrist-freeze conditions use 10 tasks × 50 starts each; π0.5 wrist black remains historical 5 × 100."],
  ["配对差数据正在读取。", "Paired differences are loading."],
  ["修复后，各路图像保留原相机槽位", "The fix preserves each camera image’s configured slot"],
  ["相机缺失会使腕部图像进入主视角槽位；已提交修复PR覆盖6个策略。", "A missing camera can shift wrist images into the agent-view slot; the submitted fix PR covers six policies."],
  ["π0.5 v044缺失主视角时修复前后的槽位布局", "π0.5 v044 slot layout before and after the fix when the agent view is missing"],
  ["提交前回归验证为旧实现21失败／6通过，修复后27/27通过。本人在相机消融中发现问题、确定修复范围、审阅改动并提交；PR提交不代表合并。", "Pre-submission regression: old 21 failed/6 passed; fixed 27/27 passed. My role was to find the issue, set scope, review changes and submit; submission does not establish a merge."],
  ["原始问题与复现", "Original issue and reproduction"],
  ["修复PR与测试证据", "Fix PR and test evidence"],
  ["腕部单因素实验", "Wrist-camera study"],
  ["相机槽位修复", "Camera-slot fix"],

  ["后续将补齐主视角单独冻结、与主实验匹配规模的主视角黑图、单路噪声及π0.5双路mask。SmolVLA和OpenVLA的扩展先核接口；OpenVLA腕部不适用。上述内容是待执行计划，不计入当前结果。", "Follow-up work will add agent-only freezing, agent blackout matched to the main-study scale, single-camera noise and π0.5 both-mask. SmolVLA/OpenVLA extensions first require interface checks; OpenVLA wrist conditions are inapplicable. These are unstarted plans, not current results."],
  ["有录像时，每个任务至多展示一段成功和一段失败选例。录像缺失不代表没做实验；全黑录像展示真实环境，策略收到的是黑图。", "When available, each task shows at most one success and one failure example. Missing video does not mean a missing experiment. All-black videos show the real environment; the policy received black images."],
  ["输入与操作示意不代表每个模型都完成了所有干预；实际范围见上方覆盖表。", "The input/operation diagram does not establish that every policy received every intervention. See the coverage table above."],

  ["三模型探索：单路黑图与双路噪声／冻结", "Three-policy exploration: single-camera black and both-camera noise/freezing"],
  ["两模型腕部主实验；主视角mask为附加条件", "Two-policy wrist study; agent masking is supplementary"],
  ["π0与π0.5腕部主实验及分区的主视角附加条件", "π0 and π0.5 wrist study, with supplementary agent masking separated"],
  ["额外检查点对照：官方 π0 / OpenPI", "Additional checkpoint control: official π0 / OpenPI"],
  ["官方π0与LeRobotπ0：每点同100初态，重复逐次展示", "Official and LeRobot π0: same 100 states per point, repeats shown individually"],
  ["查看参考复现中的三个LIBERO检查点", "Inspect the three LIBERO checkpoints in the reference comparisons"],
  ["参考复现中的三个LIBERO检查点：逐任务结果", "Three LIBERO checkpoints in the reference comparisons: per-task results"],
  ["两个模型的选例演示，不是四模型总览。同任务同初态，右侧两次策略收到黑图。", "Selected two-policy demos, not a four-policy overview. Same task/state; the two right-hand policies receive black images."],
  ["腕部主实验只覆盖π0／π0.5，主视角保持正常。正常、腕部mask和腕部冻结各500初态；π0.5腕部黑图借用同100初态的5次重复。主视角mask为附加条件，不是完整主视角实验；主视角单独冻结与单路噪声未测。", "The wrist study covers π0/π0.5 only, with the agent view live. Normal, wrist mask and wrist freeze use 500 states each; π0.5 wrist black borrows five repeats of 100 states. Agent masking is supplementary, not a full agent-view experiment. Agent-only freezing and single-camera noise are untested."],
  ["图中每点取同100初态，正常为官方93/100、LeRobot65/100；500回合运行只取每任务前10初态。LeRobot重复逐次展示，不合并Wilson区间。完整500正常96.4%／72.0%另列参考；权重与推理管线同时不同，不作单因素归因。", "Each point uses the same 100 states: normal 93/100 official and 65/100 LeRobot. Full 500 runs contribute the first 10 states per task. LeRobot repeats remain separate, without pooled Wilson intervals. Full 500 normal 96.4%/72.0% are separate references. Weights and pipelines both differ; no single-factor causal attribution."],
  ["实验范围：4 → 3 → 2", "Experiment scope: 4 → 3 → 2"],
  ["范围", "Scope"],
  ["已完成的实验", "Completed experiments"],
  ["没有覆盖的部分", "Outside coverage"],
  ["四模型", "Four policies"],
  ["全黑对照", "All-black comparison"],
  ["不是四模型都完成全部干预", "Not every intervention for every policy"],
  ["三个双视角模型", "Three dual-view policies"],
  ["单路黑图、双路噪声和双路冻结", "Single-camera black, both-camera noise/freezing"],
  ["OpenVLA仅主视角，不在此组", "OpenVLA is agent-only, outside this group"],
  ["腕部单因素主实验；主视角mask附加条件", "Wrist-treatment study; supplementary agent mask"],
  ["主视角单独冻结、单路噪声未测", "Agent-only freezing and single-camera noise untested"],
  ["官方π0为额外检查点与管线对照；P1/P2界定π0异常结果的解释，不是腕部因果验证。五项工程参考对照是另一组模型。", "Official π0 adds a checkpoint/pipeline control; P1/P2 bound the anomalous π0 result, not wrist causality. Five engineering references form a separate policy set."],
  ["双路加高斯噪声", "Both-camera Gaussian noise"],
  ["双路冻结首帧", "Both first frames frozen"],
  ["完整模型与实验覆盖", "Full policy and experiment coverage"],

  ["状态输入更新（P1）", "State-input updates (P1)"],
  ["选择外固定动作回放（P2）", "Selection-external replay (P2)"],
  ["补充结果数据加载中；可直接查看下方CSV和原始记录。", "Follow-up data is loading; CSVs and raw records are linked below."],
  ["P2将每任务预先选定的一套官方π0动作，在未参与动作选择的状态上原样回放。目标曾用于旧评测，并非隐藏测试集。", "P2 replays one preselected official π0 action sequence per task on states excluded from action selection. Targets appeared in earlier evaluations; they are not a hidden test set."],
  ["底层控制器仍有反馈；区间固定十任务，不覆盖动作来源选择或新任务泛化。不能将P2与P1的成功率相减来分配机制贡献。", "The low-level controller retains feedback. The interval fixes the ten tasks and excludes source-selection uncertainty and new-task generalization. P2 and P1 rates cannot be subtracted to assign mechanism contributions."],
  ["LeRobot π0 v044在所测冻结状态条件下均未成功；仿真环境、底层控制和动作后处理仍继续运行。", "LeRobot π0 v044 has no successes in the tested frozen-state conditions; the simulator, low-level control and action postprocessing continue running."],
  ["这测得状态更新敏感性，尚不能区分在线纠偏、动作阶段线索与输入失配。P1未保存逐步终止标记和完整图像；公开记录支持统计重算，完整NPZ审计工件不在Git内。", "This measures state-update sensitivity without separating online correction, action-phase cues and input mismatch. P1 did not save stepwise terminal flags or full images. Public records reproduce statistics; full NPZ audit artifacts remain outside Git."],
  ["早期回放与选择偏差", "Earlier replay and selection bias"],
  ["逐任务与区间 CSV", "Task results & intervals CSV"], ["逐回合 CSV", "Episode results CSV"],
  ["原始回放结果 JSON", "Raw replay outcomes JSON"], ["冻结动作 JSON", "Frozen actions JSON"],
  ["完整设计与局限", "Full protocol & limitations"], ["早期回放 CSV", "Earlier replay CSV"],
  ["三轮成功率均值", "Mean success rates across three repeats"], ["输入画面", "Image input"],
  ["实时状态", "Live state"], ["冻结首状态", "Frozen first state"],
  ["分组与重复 CSV", "Conditions & repeats CSV"], ["配对比较 CSV", "Paired comparisons CSV"],
  ["原始结果与配对", "Raw outcomes & pairing"],
  ["已完成补充实验：状态更新与选择外固定动作回放", "Completed follow-ups: state updates and selection-external replay"],
  ["完整实验与P1/P2", "Full experiments and P1/P2"],
  ["选择外固定动作回放、状态更新与解释边界", "Selection-external replay, state updates and interpretation limits"],
  ["此图保留早期选择集上的交叉回放；已完成的选择外回放和状态更新检查见下方完整实验入口。", "This figure retains earlier selection-set cross-replay; completed selection-external replay and state-update checks are in the full experiment report below."],
  ["LIBERO-Spatial 相机消融实验", "Camera ablations on LIBERO-Spatial"],
  ["LIBERO-Spatial 上四种机器人策略的相机消融实验", "Camera ablations of four robot policies on LIBERO-Spatial"],
  ["同一任务：π0.5 正常成功、涂黑失败，LeRobot π0 涂黑仍成功", "Same task: π0.5 succeeds with vision and fails with black input; LeRobot π0 still succeeds with black input"],
  ["同一任务、同一初始状态。右侧两次运行中，策略收到的是黑图。", "Same task and initial state. In the two right-hand runs, the policy receives black images."],
  ["动作来自官方π0正常运行。每任务事后挑出的最好一套为77.8%，存在选择偏差，不能当作无偏基线。固定的是高层动作，底层控制器仍有反馈；回放不识别LeRobot π0全黑成功的内部机制。", "Actions come from official π0 with normal vision. The post-hoc best sequence per task scores 77.8%, with selection bias rather than an unbiased baseline. High-level actions are fixed; the low-level controller retains feedback. Replay does not identify the mechanism of LeRobot π0 all-black success."],
  ["查看两次运行的轨迹明细", "Inspect both trajectory runs"],
  ["选择模型查看评测与基准来源", "Select a model to inspect evaluation and reference sources"],
  ["点击模型行查看来源；键盘可用上下方向键切换。", "Select a model row for sources. Use the up and down arrow keys to move between models."],
  ["点击模型名称查看来源。", "Select a model name for sources."],
  ["查看原图 SVG", "Full-size SVG"], ["逐回合数据", "Episode data"], ["结果 CSV", "Results CSV"],
  ["查看原始评测", "Raw evaluation"], ["固定版本权重", "Checkpoint revision"],
  ["评测与来源", "Evaluation & sources"],
  ["查看 LIBERO-Spatial 各任务成功率", "Inspect success by LIBERO-Spatial task"],
  ["查看 π0 分任务结果", "Inspect π0 results by task"],
  ["固定动作交叉回放、事后挑选与选择偏差的比较", "Fixed-action cross-replay, post-hoc selection, and selection bias"],
  ["从实验结论到评测入口，再到原始回合记录。", "From findings to evaluation scripts and raw episode records."],
  ["环境、权重与第一条评测命令", "Environment, checkpoints, and a first evaluation"],
  ["每个实验对应的执行与汇总入口", "Run and analysis entry points for every experiment"],
  ["成功率、配对比较与回放 CSV", "Success rates, paired comparisons, and replay CSVs"],
  ["按运行保留的逐回合结果", "Episode-level outcomes organized by run"],
  ["设计、重复运行、负结果与更正", "Designs, repeated runs, negative results, and corrections"],
  ["查看回放数据 CSV", "Open replay CSV"], ["复现与数据入口", "Reproduce & inspect"],
  ["查看实验结果", "Explore the results"], ["结果速览", "Findings at a glance"],
  ["原始评测数据", "Raw evaluations"], ["实验记录与局限", "Notes & limitations"],
  ["文档与数据", "Docs & data"], ["安装与复现", "Install & reproduce"], ["脚本索引", "Script index"],
  ["本页目录", "On this page"], ["主导航", "Main navigation"], ["跳到正文", "Skip to content"],
  ["所有相机涂黑", "All cameras black"], ["噪声与冻结", "Noise & frozen frames"],
  ["轨迹比较", "Trajectories"], ["单路相机", "Single camera"], ["开环回放", "Open-loop replay"],
  ["本地录像", "Local recordings"], ["结果表", "Result tables"], ["概览", "Overview"],
  ["切换为深色", "Switch to dark theme"], ["切换为浅色", "Switch to light theme"],
  ["深色", "Dark"], ["浅色", "Light"],
  ["在所测全黑回合中，三个检查点均未成功；LeRobot π0 v044及其管线五次成功率为53–56%。另对五个公开权重做了参考对照。", "In the tested all-black episodes, three checkpoints completed no tasks. LeRobot π0 v044 with its pipeline scored 53–56% across five runs. Five public checkpoints were also evaluated against references."],
  ["每个模型评测500回合。本项目将本仓库95%区间与参考范围（报告的±值、按回合数估计的区间，或单点）比较，重叠记为达到复现判据；这不是性能等效检验。", "Each model is evaluated for 500 episodes. The repo criterion compares its 95% interval with a reference range: a reported ± value, an interval estimated from episode counts, or a single point. Overlap meets the criterion; this is not an equivalence test."],
  ["SmolVLA使用仅在LIBERO-Spatial训练的公开权重，n_action_steps=10，与论文四套件训练配置不同。点击模型行可核对参考出处与原始评测。", "SmolVLA uses a public checkpoint trained on LIBERO-Spatial only, with n_action_steps=10. Its training configuration differs from the paper's four-suite setup. Select a model row for reference sources and raw evaluations."],
  ["早期π0相机实验使用LeRobot v044，一组500回合正常评测为73%。官方π0/OpenPI的全黑对照为0/100（1.5节）；结果限于各自所测检查点、管线和干预，不能推广到所有π0。", "Earlier π0 camera runs use LeRobot v044; one 500-episode normal evaluation scores 73%. Official π0/OpenPI scores 0/100 in the all-black control (section 1.5). Results concern each tested checkpoint, pipeline and intervention, not π0 in general."],
  ["每格是该任务 50 回合的成功率（%）。列标题是“拿起黑碗并放到盘子上”里碗的初始位置。", "Each cell is the success rate (%) over 50 episodes of that task. Column headers give where the bowl starts in \"pick up the black bowl and place it on the plate\"."],
  ["相机消融只改变画面输入；OpenVLA只接收主视角和指令，其余三个检查点还接收腕部画面与状态。", "Camera ablations alter image inputs. OpenVLA uses the agent view and instruction; the other three checkpoints also receive wrist images and state."],
  ["早期相机消融每次100回合，按相同初始状态比较。区间取决于配对与重复结构，不设统一的13点阈值；π0早期同条件重复最多相差18点。", "Earlier camera runs use 100 matched initial states. Uncertainty depends on pairing and repeats, not a universal 13-point threshold; earlier pi0 repeats differed by up to 18 points."],
  ["OpenVLA为220控制步，其他LIBERO模型客户端为280步，均另有10步等待。对已有回合统一220步截止计分后，首页全黑对照数字不变；这仍不是完整同协议排名。", "OpenVLA allows 220 control steps; other LIBERO model clients allow 280, each with ten settling steps. A 220-step recount preserves the headline blackout table; it is still not a complete common-protocol ranking."],
  ["协议与验收范围", "Protocols & audit scope"],
  ["三个检查点在所测全黑回合中均未成功完成任务；LeRobot π0 v044仍有一半以上成功。", "Three checkpoints completed no tested all-black episode; LeRobot pi0 v044 still succeeded in more than half."],
  ["π0 各任务的成功次数（每个任务 10 回合）：全涂黑后的失败集中在三个任务上。", "π0 successes per task (10 episodes each): the failures with black cameras are concentrated in three tasks."],
  ["所测π0.5和SmolVLA检查点对首帧冻结敏感；π0本组全黑运行的成功率低于正常运行。", "The tested π0.5 and SmolVLA checkpoints are sensitive to first-frame freezing. The π0 all-black runs in this group score below their normal runs."],
  ["各干预条件每次100回合、重复两次（同脚本、同种子）；SmolVLA未单独重跑正常条件。噪声标准差为0.1。冻结真实首帧同时改变内容更新和图像—状态同步，不能视为整体分布内干预。所测π0.5和SmolVLA腕部涂黑降幅较大；这不构成普遍的相机重要性排序。π0的单路涂黑、噪声和冻结两次相差9到18点；腕部涂黑另三次为72、67、70，尚不能据此认定其他干预没有作用。", "Each intervention uses 100 episodes per run and two repeats with the same scripts and seed; SmolVLA has no separate normal rerun. Noise standard deviation is 0.1. First-frame freezing changes both content updates and image–state synchronization, so the joint input is not guaranteed to remain in-distribution. Wrist blackout causes larger decreases for the tested π0.5 and SmolVLA checkpoints; this is not a universal camera-importance ranking. π0 repeats differ by 9–18 points under single-camera blackout, noise and freezing; three further wrist-black runs score 72, 67 and 70. These observations do not establish that other interventions have no effect."],
  ["按全黑成功率事后筛选的任务组中，正常与全黑的平均轨迹差与正常重跑参考接近；任务7的差异较大。这是描述性比较，未证明轨迹等效。", "In task groups selected post hoc by all-black success, mean normal-versus-black path differences are close to the normal-rerun reference. Task 7 has larger differences. This is descriptive, not evidence of trajectory equivalence."],
  ["各任务的末端路线差异（cm，动态时间规整后的平均点距）。整套比较跑了两次；标出的是全涂黑后成功不到一半的任务。", "End-effector path difference per task (cm, mean point distance after dynamic time warping). The whole comparison was run twice; tasks where blind π0 succeeds less than half the time are highlighted."],
  ["正常重跑参考剔除了近乎重合的任务（第1次0–3，第2次0），其余任务平均差为3.4和3.3 cm；全黑成功至少一半的事后任务组为2.8和3.2 cm。两组任务构成不同，未做轨迹等效检验。任务9两次差为7.8和4.9 cm，结果没有任务7清楚。这不能识别跟随物体或固定动作机制；固定动作回放见完整实验1.6节。", "The normal-rerun reference excludes nearly overlapping tasks (0–3 in run 1, task 0 in run 2), averaging 3.4 and 3.3 cm on the rest. Task groups selected post hoc for at least half of all-black episodes succeeding average 2.8 and 3.2 cm. The groups differ; no trajectory-equivalence test was performed. Task 9 differs by 7.8 and 4.9 cm and is less clear than task 7. This does not identify object tracking or fixed-action mechanisms; see experiment section 1.6 for replay."],
  ["每个任务一段成功、一段失败的录像。全涂黑的录像是环境的真实渲染，模型当时收到的是黑图。", "One successful and one failed episode per task. Recordings of the all-black runs show the simulator's real rendering; the model received black images."],
  ["回放视频体积大，没有随仓库发布。在本地把评测输出的 videos/ 放到 dashboard/data/<run>/ 下，就能在这里播放。", "Replay videos are too large to publish with the repository. Put each run's videos/ folder under dashboard/data/<run>/ locally to play them here."],
  ["置信区间为二项分布的正态近似。全部数据、脚本与说明见 GitHub 仓库。", "Confidence intervals use the normal approximation to the binomial. All data, scripts and notes are in the GitHub repository."],
  ["达到本项目参考对照判据的公开权重", "public checkpoints meeting the repo comparison criterion"],
  ["LeRobot π0 v044 全黑成功率", "LeRobot π0 v044 success with all cameras black"],
  ["π0.5 画面冻结后的成功率", "π0.5 success rate with the image frozen"],
  ["整个回合只给第一帧画面（%），各 100 回合", "first frame only for the whole episode (%), 100 episodes each"],
  ["降到 0%：", "Drop to 0%: "],
  ["SmolVLA 论文 Table 2（每任务 10 次）；该权重只在 LIBERO-Spatial 上训练，评测用 n_action_steps=10", "SmolVLA paper, Table 2 (10 episodes per task); this checkpoint was trained on LIBERO-Spatial only and is evaluated with n_action_steps=10"],
  ["OpenPI LIBERO README（LeRobot 文档复现为 97.0%）", "OpenPI LIBERO README (the LeRobot docs report 97.0%)"],
  ["openvla README（3 种子 × 500 回合，A100）", "openvla README (3 seeds × 500 episodes, A100)"],
  ["LeRobot 模型卡（500 回合；原版 DP 仓库同等模型 64.2%）", "LeRobot model card (500 episodes; the equivalent model in the original DP repo scores 64.2%)"],
  ["HF 仓库自带 eval_info.json（500 回合）", "eval_info.json shipped in the HF repo (500 episodes)"],
  ["π0.5对所测腕部干预高度敏感；LeRobot π0 v044配对差的95%区间落在事前±8点范围内。", "π0.5 is highly sensitive to the tested wrist interventions. LeRobot π0 v044 paired-difference 95% intervals fall inside the advance-recorded ±8-point margin."],
  ["每个条件 500 回合（10 个任务 × 50 个初始状态，各条件初始状态相同；π0.5 腕部涂黑一项是同一组 100 个初始状态跑 5 次）。“屏蔽”指在模型内部把这一路相机的槽位换成空相机占位、掩码置 0；“冻结”指整个回合只给第一帧的真实画面。π0 与双相机按初始状态配对，各条件差值的 95% 区间都在预设的 ±8 个百分点以内。逐回合结果见仓库的 results/single_camera.csv。", "500 episodes per condition (10 tasks × 50 initial states, the same initial states for every condition; π0.5 wrist black is the same 100 initial states run 5 times). \"Dropped\" fills the camera's slot inside the model with the empty-camera placeholder and sets its mask to 0; \"frozen\" gives the real first-frame image for the whole episode. Paired by initial state against both cameras, every π0 difference has a 95% interval inside the pre-set ±8-point margin. Per-episode results are in results/single_camera.csv in the repository."],
  ["官方π0/OpenPI在所测全黑与腕部屏蔽条件下均为0/100，主视角屏蔽为77/100。LeRobot v044全黑仍有成功，但两边权重与管线不同。", "Official π0/OpenPI scores 0/100 under the tested all-black and wrist-masked conditions, and 77/100 with the agent view masked. LeRobot v044 retains all-black successes, but weights and pipelines differ."],
  ["官方π0使用Physical Intelligence的pi0_libero检查点，在OpenPI管线下正常500回合为96.4%（256渲染），初始状态协议与1.4节匹配。各视觉干预100回合；360复测正常99/100，全黑和双槽屏蔽均为0/100。LeRobot侧为360渲染；另行试用的HF检查点冒烟0/50，且未通过同源性核验，不是同权重的管线对照。此对照未隔离权重、转换与其他推理差异。设计记录见仓库docs/NOTES_CN.md，汇总见results/official_pi0_summary.csv。", "Official π0 uses Physical Intelligence's pi0_libero checkpoint in OpenPI: 96.4% over 500 normal episodes at 256 rendering, with initial-state protocols matched to section 1.4. Visual interventions use 100 episodes each. At 360, normal scores 99/100; all black and both slots masked score 0/100. LeRobot uses 360 rendering; a separate HF candidate scores 0/50 and fails identity verification, so it is not a same-weight pipeline control. Weights, conversion and other inference differences remain unseparated. See docs/NOTES.md for designs and results/official_pi0_summary.csv for the summary."],
  ["官方 π0 与 LeRobot π0 去掉相机后的成功率", "Official π0 vs. LeRobot π0 with cameras removed"],
  ["官方 π0 对照", "Official π0 control"],
  ["去掉腕部相机：每个条件 500 回合", "Wrist camera removed: 500 episodes per condition"],
  ["测试时去掉一路相机后的成功率", "Success rate with one camera removed at test time"],
  ["策略输入与各实验的干预对象", "Policy inputs and intervention targets"],
  ["π0 有无相机输入时的末端路线", "End-effector paths of π0 with and without camera input"],
  ["正常与全涂黑成功率对比", "Normal vs. all-black success rate"], ["各模型成功率对比", "Success rate by model"],
  ["四个机器人策略在 LIBERO-Spatial 上的相机输入消融", "Camera-input ablations of four robot policies on LIBERO-Spatial"],
  ["LIBERO-Spatial 各任务成功率", "LIBERO-Spatial success rate per task"],
  ["末端轨迹的描述性比较", "Descriptive end-effector trajectory comparison"],
  ["单路相机、噪声、冻结画面", "One camera, noise, frozen image"],
  ["所有相机涂黑", "All cameras black"],
  ["全涂黑时成功次数（/10）", "Blind π0 successes (of 10)"], ["正常 vs 正常重跑", "Normal vs. normal re-run"], ["全涂黑 vs 正常", "All black vs. normal"], ["π0.5 vs π0，都正常", "π0.5 vs. π0, both normal"],
  ["本仓库（横线 = 95% 置信区间）", "This repo (bar = 95% confidence interval)"],
  ["盘子与小烤碗之间", "between plate and ramekin"], ["木柜上层抽屉里", "in top drawer of cabinet"], ["小烤碗旁", "next to ramekin"], ["小烤碗上", "on ramekin"],
  ["桌子中央", "table centre"], ["饼干盒上", "on cookie box"], ["饼干盒旁", "next to cookie box"], ["灶台上", "on stove"], ["盘子旁", "next to plate"], ["木柜顶上", "on top of cabinet"],
  [/第 (\d+) 回合/g, "episode $1"], [/(\d+) 回合/g, "$1 episodes"], [/任务 (\d)/g, "Task $1"], [/第 (\d) 次/g, "run $1"],
  ["本仓库：", "This repo: "], ["原作者基准：", "Authors' reference: "], ["本仓库", "This repo"], ["原作者基准", "Authors' reference"],
  ["复现结果", "Reproduction"], ["相机消融", "Camera ablations"], ["回放", "Replays"], ["表格视图", "Table view"], ["图表视图", "Chart view"],
  ["加高斯噪声", "Gaussian noise"], ["冻结首帧", "Frozen first frame"], ["只涂主视角", "Agent-view black"], ["只涂腕部", "Wrist black"],
  ["正常画面", "Normal"], ["全涂黑", "All black"], ["正常", "Normal"], ["待评测", "pending"], ["评测中", "running"],
  ["回合数", "Episodes"], ["仿真器", "Simulator"], ["模型", "Model"], ["任务", "Task"], ["权重", "Checkpoint"],
  ["总体", "Overall"], ["奖励 ", "reward "], ["成功", "success"], ["失败", "fail"],
  ["（", " ("], ["）", ")"], ["，", ", "], ["：", ": "], ["；", "; "],
];
const TRANSLATIONS = [...DICT].sort((a, b) => (typeof b[0] === "string" ? b[0].length : -1) - (typeof a[0] === "string" ? a[0].length : -1));
function trStr(t) { for (const [a, b] of TRANSLATIONS) t = typeof a === "string" ? t.split(a).join(b) : t.replace(a, b); return t; }
function trNode(n) {
  if (n.nodeType === 3) { const t = trStr(n.nodeValue); if (t !== n.nodeValue) n.nodeValue = t; return; }  // 只在有变化时写回，否则会反复触发观察器
  if (n.nodeType !== 1 || n.tagName === "SCRIPT" || n.tagName === "STYLE") return;
  for (const a of ["title", "aria-label", "alt"]) if (n.hasAttribute(a)) { const t = trStr(n.getAttribute(a)); if (t !== n.getAttribute(a)) n.setAttribute(a, t); }
  n.childNodes.forEach(trNode);
}
$("langBtn").textContent = LANG === "en" ? "中文" : "English";
$("langBtn").onclick = () => { location.search = "?lang=" + (LANG === "en" ? "zh" : "en"); };
// README 用的两张图：线上在仓库的 media/ 下；本地没有这些文件时整块隐藏
for (const [id, name] of [["figLoop", "evaluation_loop"], ["figSlots", "camera_slot_fix"], ["figInputs", "inputs"], ["figTraj", "trajectory"], ["figSingle", "single_camera"], ["figOfficial", "official_pi0"], ["figReplay", "open_loop_replay"]]) {
  $(id).onerror = () => $(id).closest(".fig").classList.add("hidden");
  $(id).src = `../media/${LANG === "en" ? "" : "zh/"}${name}.svg?v=interview-4`;
}
$("figInputsMobile").srcset = `../media/${LANG === "en" ? "" : "zh/"}inputs-mobile.svg?v=interview-4`;
if (LANG === "en") {
  document.documentElement.lang = "en"; document.title = trStr(document.title);
  new MutationObserver(ms => ms.forEach(m => m.type === "characterData" ? trNode(m.target) : m.addedNodes.forEach(trNode)))
    .observe(document.body, { childList: true, subtree: true, characterData: true });
  trNode(document.body);
}

const done = R.filter(r => r.status === "done");
// 本项目参考对照判据：评测95%区间与来源±值、估计区间或单点重叠；非等效检验。
const reproduced = (r) => { const b = r.baseline_pm ?? r.baseline_ci ?? 0; return Math.abs(r.pc - r.baseline_pc) <= r.ci + b; };
const BO = window.BLACKOUT || { summary: [], runs: [] };
const FU = window.FOLLOWUP || {};
const MNAME = { pi0: "π0", "pi0.5": "π0.5" };
const HAS_CORE_DATA = R.length > 0 && Array.isArray(window.BLACKOUT?.summary) && Array.isArray(window.BLACKOUT?.runs)
  && Array.isArray(FU.pi0_black_runs) && FU.pi0_black_runs.length > 0
  && Array.isArray(FU.perturb) && FU.perturb.some(r => r.model === "pi0.5");

// Evaluation rates come from public records; engineering counts describe the submitted PR's historical checks.
const wristStudy = Array.isArray(FU.wrist_study) ? FU.wrist_study : [];
const wristPi05 = wristStudy.find(row => row.model === "pi0.5");
if (HAS_CORE_DATA) {
  const zero = BO.summary.filter(r => sum(r.black) === 0).map(r => MNAME[r.model] || r.model);
  const wrist = wristPi05?.conditions;
  const cards = [
    [`${Math.min(...FU.pi0_black_runs)}–${Math.max(...FU.pi0_black_runs)}%`, "全黑对照：LeRobot π0 v044全黑成功率", "其他所测检查点为0%：" + zero.join(" · "), "#blackout"],
    wrist ? [`${wrist.normal.pc} → ${wrist.mask.pc}%`, "腕部单因素实验：π0.5屏蔽腕部后的成功率", `只冻结腕部为${wrist.freeze.pc}%；每条件${wrist.normal.episodes}回合`, "#single-camera"]
      : ["—", "腕部单因素实验数据尚未加载", "可直接核对下方结果与CSV", "#single-camera"],
    [LANG === "en" ? "6 policies" : "6个策略", "相机槽位修复：6个策略、27项回归用例", "提交前：旧21失败／6通过 → 修后27/27通过", "#engineering"],
  ];
  const markup = cards.map(([v, k, d, href]) => `<a class="key" href="${href}"><span class="v">${v}</span><span class="key-copy"><span class="k">${k}</span><span class="d">${d}</span></span><svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m9 5 7 7-7 7"/></svg></a>`).join("");
  $("keys").innerHTML = LANG === "en" ? trStr(markup) : markup;
} else {
  $("keys").innerHTML = LANG === "en"
    ? '<p class="pending" role="status">Results data could not be loaded. Reload the page or use the <a href="#resources">docs and data links</a>.</p>'
    : '<p class="pending" role="status">结果数据未加载。请刷新页面，或查看<a href="#resources">文档与数据</a>。</p>';
}
const pairedRows = wristStudy.filter(row => row.paired_mask);
$("wristPaired").textContent = pairedRows.length === 2
  ? (LANG === "en" ? "Wrist mask minus normal, paired by task/start (pp; 95% normal approximation): " : "腕部屏蔽减正常，按任务／初态配对（百分点；95%正态近似）：")
    + pairedRows.map(row => `${MNAME[row.model] || row.model} ${row.paired_mask.difference_pp} [${row.paired_mask.ci95_lo}, ${row.paired_mask.ci95_hi}]`).join("; ")
  : (LANG === "en" ? "Paired differences could not be loaded; use the linked CSV." : "配对差未加载，可查看链接中的CSV。");

// ---- dot plot
let selectedModel = 0;
function selectModel(index, focus = false) {
  selectedModel = index;
  const r = R[index];
  if (!r) return;
  for (const el of document.querySelectorAll("[data-model-index]")) {
    const active = Number(el.dataset.modelIndex) === index;
    el.setAttribute("aria-pressed", String(active));
    if (el.classList.contains("chart-row")) el.tabIndex = active ? 0 : -1;
  }
  const pm = r.baseline_pm ?? r.baseline_ci;
  const [checkpoint, revision] = r.checkpoint.split("@");
  const content = `<h4>${r.model} <span>· ${r.task}</span></h4>` +
    `<dl><div><dt>本仓库</dt><dd>${fmt(r.pc)} <span>± ${r.ci.toFixed(1)} · 95% CI · ${r.n} 回合</span></dd></div>` +
    `<div><dt>原作者基准</dt><dd>${fmt(r.baseline_pc)}${pm != null ? ` <span>± ${pm.toFixed(1)}</span>` : ""}</dd></div></dl>` +
    `<p class="reference-source">${r.baseline_src}</p>` +
    `<div class="detail-links"><a href="data/${r.id}/eval_info.json" target="_blank" rel="noopener">查看原始评测</a>` +
    `<a href="https://huggingface.co/${checkpoint}/tree/${revision}" target="_blank" rel="noopener">固定版本权重 <code>${revision}</code></a></div>`;
  $("modelDetail").innerHTML = LANG === "en" ? trStr(content) : content;
  if (focus) document.querySelector(`.chart-row[data-model-index="${index}"]`).focus({ preventScroll: true });
}
function drawChart() {
  if (!HAS_CORE_DATA) return;
  const svg = $("chart"), wrap = $("chartWrap");
  const W = wrap.clientWidth; if (!W) return;  // 表格视图下图表被隐藏，宽度为 0
  const labelW = Math.min(190, W * 0.34), padR = 24, rowH = 64, top = 8, axisH = 28;
  const H = top + rowH * R.length + axisH;
  svg.setAttribute("width", W); svg.setAttribute("height", H);
  const x = (v) => labelW + (W - labelW - padR) * v / 100;
  let s = "";
  for (let t = 0; t <= 100; t += 20) {
    s += `<line x1="${x(t)}" x2="${x(t)}" y1="${top}" y2="${H - axisH}" stroke="var(--grid)"/>`;
    s += `<text x="${x(t)}" y="${H - 8}" text-anchor="middle">${t}%</text>`;
  }
  R.forEach((r, i) => {
    const cy = top + rowH * i + rowH / 2;
    s += `<g class="chart-row" role="button" data-model-index="${i}" tabindex="${i === selectedModel ? 0 : -1}" aria-pressed="${i === selectedModel}" aria-label="${r.model}"><rect class="row-highlight" x="1" y="${top + rowH * i}" width="${W - 2}" height="${rowH}" rx="4"/>`;
    s += `<text class="lbl" x="8" y="${cy - 4}">${r.model}</text><text x="8" y="${cy + 13}">${W < 500 ? r.sim : `${r.task} · ${r.sim}`}</text>`;
    if (r.baseline_pc != null) {
      const bx = x(r.baseline_pc), pm = r.baseline_pm ?? r.baseline_ci;
      if (pm) s += `<line x1="${x(r.baseline_pc - pm)}" x2="${x(r.baseline_pc + pm)}" y1="${cy + 9}" y2="${cy + 9}" stroke="var(--series-2)" stroke-width="2" stroke-linecap="round"/>`;
      s += `<rect x="${bx - 5}" y="${cy + 4}" width="10" height="10" transform="rotate(45 ${bx} ${cy + 9})" fill="var(--series-2)" stroke="var(--surface-1)" stroke-width="2"/>`;
    }
    if (r.pc != null) {
      const px = x(r.pc);
      s += `<line x1="${x(r.pc - r.ci)}" x2="${x(r.pc + r.ci)}" y1="${cy - 7}" y2="${cy - 7}" stroke="var(--series-1)" stroke-width="2" stroke-linecap="round"/>`;
      s += `<circle cx="${px}" cy="${cy - 7}" r="6" fill="var(--series-1)" stroke="var(--surface-1)" stroke-width="2"/>`;
      s += `<text class="val" x="${px}" y="${cy - 17}" text-anchor="middle">${fmt(r.pc)}</text>`;
    } else {
      s += `<text x="${x(2)}" y="${cy - 3}">待评测</text>`;
    }
    s += `<rect x="0" y="${cy - rowH / 2}" width="${W}" height="${rowH}" fill="transparent"/></g>`;
  });
  svg.innerHTML = s;
  svg.querySelectorAll(".chart-row").forEach(el => {
    el.addEventListener("click", () => selectModel(Number(el.dataset.modelIndex)));
    el.addEventListener("keydown", e => {
      let index = Number(el.dataset.modelIndex);
      if (e.key === "ArrowDown") index = (index + 1) % R.length;
      else if (e.key === "ArrowUp") index = (index + R.length - 1) % R.length;
      else if (e.key === "Home") index = 0;
      else if (e.key === "End") index = R.length - 1;
      else if (!["Enter", " "].includes(e.key)) return;
      e.preventDefault();
      selectModel(index, true);
    });
  });
}

// ---- table view
$("tbl").innerHTML = `<table><thead><tr><th>模型</th><th>任务</th><th>仿真器</th><th>本仓库</th><th>95% CI</th><th>回合数</th><th>原作者基准</th><th>权重</th></tr></thead><tbody>` +
  R.map((r, i) => `<tr><th scope="row"><button class="model-select" data-model-index="${i}" aria-pressed="${i === selectedModel}">${r.model}</button></th><td>${r.task}</td><td>${r.sim}</td><td>${fmt(r.pc)}</td><td>${r.ci != null ? "± " + r.ci.toFixed(1) : "—"}</td><td>${r.n ?? "—"}</td><td>${fmt(r.baseline_pc)}${r.baseline_pm != null ? " ± " + r.baseline_pm : ""}</td><td><code>${r.checkpoint}</code></td></tr>`).join("") + `</tbody></table>`;
$("tbl").querySelectorAll(".model-select").forEach(el => el.onclick = () => selectModel(Number(el.dataset.modelIndex)));
$("tblBtn").addEventListener("click", (e) => {
  const on = $("tbl").classList.contains("hidden");
  e.currentTarget.setAttribute("aria-expanded", String(on));
  e.currentTarget.textContent = on ? "图表视图" : "表格视图";
  $("tbl").classList.toggle("hidden", !on); $("chartWrap").classList.toggle("hidden", on); $("legend").classList.toggle("hidden", on);
  $("chartHelp").textContent = on ? "点击模型名称查看来源。" : "点击模型行查看来源；键盘可用上下方向键切换。";
  if (LANG === "en") trNode($("chartHelp"));
  if (!on) drawChart();  // 隐藏期间若缩放过窗口，切回来时重画
});

// ---- per-task matrix (LIBERO-Spatial)
const RAMP = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"];
function cellColor(p) { const x = Math.max(0, Math.min(1, (p - 50) / 50)); const i = Math.round(x * (RAMP.length - 1)); return [RAMP[i], i >= 8 ? "#ffffff" : "#000000"]; }
function drawMatrix() {
  const L = R.filter(r => r.task === "LIBERO-Spatial"), T = window.LIBERO_TASKS || [];
  let h = `<thead><tr><th></th>${T.map(n => `<th><div class="colh">${n}</div></th>`).join("")}<th>总体</th></tr></thead><tbody>`;
  for (const r of L) {
    h += `<tr><th class="row">${r.model}</th>`;
    for (let i = 0; i < T.length; i++) {
      const t = (r.tasks || []).find(x => x.id === i);
      if (!t) { h += `<td class="na">—</td>`; continue; }
      const p = 100 * t.ok / t.n, [bg, fg] = cellColor(p);
      h += `<td style="background:${bg};color:${fg}" title="${r.model} · ${T[i]}：${t.ok}/${t.n}（${p.toFixed(0)}%）">${p.toFixed(0)}</td>`;
    }
    const [bg, fg] = r.pc != null ? cellColor(r.pc) : ["", ""];
    h += r.pc != null ? `<td style="background:${bg};color:${fg};font-weight:600" title="${r.model} 总体 ${fmt(r.pc)}（${r.n} 回合）">${r.pc.toFixed(1)}</td>` : `<td class="na">评测中</td>`;
    h += `</tr>`;
  }
  $("matrix").innerHTML = h + "</tbody>";
}

// 成功次数的格子：不足一半用灰底，其余按色阶
function countCell(v, n, title) {
  const p = 100 * v / n, [bg, fg] = cellColor(Math.max(50, p));
  return `<td style="background:${p < 50 ? "var(--grid)" : bg};color:${p < 50 ? "var(--text-primary)" : fg}" title="${title}：${v}/${n}">${v}</td>`;
}
// 正常 → 全涂黑 的哑铃图
function dumbbell(svg, rows, labelMax) {
  const W = svg.parentNode.clientWidth; if (!W) return;
  const labelW = Math.min(labelMax, W * 0.36), padR = 24, rowH = 44, top = 20, axisH = 26;
  const H = top + rowH * rows.length + axisH, x = v => labelW + (W - labelW - padR) * v / 100;
  let s = "";
  for (let v = 0; v <= 100; v += 25) s += `<line x1="${x(v)}" x2="${x(v)}" y1="${top - 8}" y2="${H - axisH}" stroke="var(--grid)"/><text x="${x(v)}" y="${H - 8}" text-anchor="middle">${v}%</text>`;
  rows.forEach(([name, a, b], i) => {
    const cy = top + rowH * i + rowH / 2 - 8;
    s += `<text class="lbl" x="0" y="${cy + 4}">${name}</text>`;
    s += `<line x1="${x(b)}" x2="${x(a)}" y1="${cy}" y2="${cy}" stroke="var(--border)" stroke-width="2"/>`;
    s += `<circle cx="${x(a)}" cy="${cy}" r="6" fill="var(--series-1)" stroke="var(--surface-1)" stroke-width="2"><title>${name} 正常 ${a}%</title></circle>`;
    s += `<circle cx="${x(b)}" cy="${cy}" r="5" fill="var(--surface-1)" stroke="var(--series-2)" stroke-width="2"><title>${name} 全涂黑 ${b}%</title></circle>`;
    s += `<text class="val" x="${x(a)}" y="${cy - 11}" text-anchor="middle">${a}</text><text class="val" x="${x(b) + (b < 8 ? 12 : 0)}" y="${cy - 11}" text-anchor="middle">${b}</text>`;
  });
  svg.setAttribute("width", W); svg.setAttribute("height", H); svg.innerHTML = s;
}

// ---- 1.1 全涂黑
function drawBlackout() {
  dumbbell($("bchart"), BO.summary.map(r => [MNAME[r.model] || r.model, sum(r.normal), sum(r.black)]), 110);
  const p0 = BO.summary.find(r => r.model === "pi0"), T = window.LIBERO_TASKS || [];
  if (!p0) return;
  let h = `<thead><tr><th></th>${T.map(n => `<th><div class="colh">${n}</div></th>`).join("")}</tr></thead><tbody>`;
  for (const [lab, arr] of [["正常", p0.normal], ["全涂黑", p0.black]])
    h += `<tr><th class="row">${lab}</th>` + arr.map((v, i) => countCell(v, 10, `π0 ${lab} · ${T[i]}`)).join("") + "</tr>";
  $("bmatrix").innerHTML = h + "</tbody>";
}

// ---- 1.2 扰动矩阵、1.3 分任务路线差异
function drawFollowup() {
  const PT = Object.fromEntries((FU.perturb || []).map(r => [r.model, r]));
  const cols = [["normal", "正常"], ["noise", "双路加高斯噪声"], ["freeze", "双路冻结首帧"], ["agent_black", "只涂主视角"], ["wrist_black", "只涂腕部"], ["all_black", "全涂黑"]];
  let h = `<thead><tr><th></th>${cols.map(c => `<th>${c[1]}</th>`).join("")}</tr></thead><tbody>`;
  const P2 = Object.fromEntries((FU.perturb2 || []).map(r => [r.model, r]));
  for (const c of FU.cam || []) {
    const name = MNAME[c.model] || c.model;
    [{ ...PT[c.model], ...c }, P2[c.model]].forEach((r, i) => {  // 第 1 次、第 2 次运行各一行
      if (!r) return;
      h += `<tr><th class="row">${name} · 第 ${i + 1} 次</th>` + cols.map(([k, lab]) => r[k] == null ? `<td class="na">—</td>` : countCell(r[k], 100, `${name} 第 ${i + 1} 次 · ${lab}`)).join("") + "</tr>";
    });
  }
  $("cammatrix").innerHTML = h + "</tbody>";

  const names = window.LIBERO_TASKS || [];
  if (!FU.traj) return;
  const labels = ["正常 vs 正常重跑", "全涂黑 vs 正常", "π0.5 vs π0，都正常"];  // 与 traj_analyze.json 里 pairs 的顺序一致
  h = `<thead><tr><th></th>${names.slice(0, 10).map((nm, i) => `<th title="${nm}">任务 ${i}</th>`).join("")}</tr></thead><tbody>`;
  [FU.traj, FU.traj2].filter(Boolean).forEach((T, n) => {
    const succ = T.successes_by_task.traj_pi0_black, fail = succ.map(v => v < 5);
    h += `<tr><th class="row" colspan="11" style="text-align:left">第 ${n + 1} 次</th></tr>`;
    h += `<tr><th class="row">全涂黑时成功次数（/10）</th>` + succ.map((v, i) => `<td class="${fail[i] ? "hot" : "plain"}" title="${names[i]}">${v}</td>`).join("") + "</tr>";
    Object.values(T.pairs).forEach((p, k) => {
      h += `<tr><th class="row">${labels[k]}</th>` + p.dtw_by_task.map((v, i) => `<td class="${k === 1 && fail[i] ? "hot" : "plain"}" title="${names[i]}">${v.toFixed(1)}</td>`).join("") + "</tr>";
    });
  });
  $("trajmatrix").innerHTML = h + "</tbody>";
}

// ---- 03 回放：6 次正常评测 + 3 次全涂黑评测共用一排筛选
const RUNS = [...R.map(r => ({ ...r, label: `${r.model} · ${r.task}` })), ...BO.runs.map(r => ({ ...r, label: `${r.model} · 全涂黑` }))];
let cur = RUNS[0]?.id;
function drawVideos() {
  $("filters").innerHTML = RUNS.map(r => `<button class="chip" data-id="${r.id}" aria-pressed="${r.id === cur}">${r.label}</button>`).join("");
  $("filters").querySelectorAll(".chip").forEach(b => b.onclick = () => { cur = b.dataset.id; drawVideos(); });
  const r = RUNS.find(x => x.id === cur);
  $("videos").innerHTML = `<div class="grid">` + (r?.videos || []).map(v => `<div class="vid"><video src="${v.src}#t=0.1" controls muted loop playsinline preload="metadata"></video>
    <div class="meta"><span>${v.task !== r.task ? v.task + " · " : ""}第 ${v.ep} 回合${v.reward != null ? " · 奖励 " + v.reward : ""}</span><span class="st ${v.success ? "ok" : "fail"}"><i>${v.success ? "✓" : "✗"}</i>${v.success ? "成功" : "失败"}</span></div></div>`).join("") + `</div>`;
}
// 视频不随仓库发布：加载不到时整块换成一句说明，而不是一排空播放器。
// 404 时浏览器不一定触发 <video> 的 error 事件，所以先探测一次，error 事件只作兜底。
function noVideos() {
  $("replayBody").innerHTML = `<p class="pending">回放视频体积大，没有随仓库发布。在本地把评测输出的 videos/ 放到 dashboard/data/&lt;run&gt;/ 下，就能在这里播放。</p>`;
}
addEventListener("error", e => {
  if (e.target.tagName === "VIDEO" && $("replayBody").contains(e.target)) noVideos();
}, true);
const probe = RUNS[0]?.videos?.[0]?.src;
if (probe && location.protocol !== "file:")
  fetch(probe, { method: "HEAD" }).then(r => { if (r.ok) drawVideos(); else noVideos(); }).catch(noVideos);
else if (probe) drawVideos();
else noVideos();

if (HAS_CORE_DATA) { drawChart(); selectModel(selectedModel); drawMatrix(); drawBlackout(); drawFollowup(); }
addEventListener("resize", () => { if (HAS_CORE_DATA) { drawChart(); drawBlackout(); } });

// Theme and wayfinding share the existing light/dark palette.
let savedTheme;
try { savedTheme = localStorage.getItem("camera-theme"); } catch { /* Storage can be disabled. */ }
if (["light", "dark"].includes(savedTheme)) document.documentElement.dataset.theme = savedTheme;
function themeLabel() {
  const dark = document.documentElement.dataset.theme === "dark" || (!document.documentElement.dataset.theme && matchMedia("(prefers-color-scheme: dark)").matches);
  $("themeBtn").textContent = LANG === "en" ? (dark ? "Light" : "Dark") : (dark ? "浅色" : "深色");
  $("themeBtn").setAttribute("aria-pressed", String(dark));
  $("themeBtn").setAttribute("aria-label", LANG === "en" ? `Switch to ${dark ? "light" : "dark"} theme` : `切换为${dark ? "浅色" : "深色"}`);
  return dark;
}
$("themeBtn").onclick = () => {
  const next = themeLabel() ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  try { localStorage.setItem("camera-theme", next); } catch { /* Optional preference. */ }
  themeLabel();
};
themeLabel();
for (const link of document.querySelectorAll("[data-doc]")) {
  const anchor = LANG === "en" ? link.dataset.anchorEn : link.dataset.anchorZh;
  link.href = `https://github.com/chaoshengsc/libero-camera-ablation/blob/main/${link.dataset.doc}${LANG === "en" ? "" : "_CN"}.md${anchor ? "#" + anchor : ""}`;
}
for (const link of document.querySelectorAll("[data-figure]")) link.href = `../media/${LANG === "en" ? "" : "zh/"}${link.dataset.figure}.svg`;
const followups = window.FOLLOWUP_RESULTS;
if (followups?.p1 && followups?.p2) {
  const { p1, p2 } = followups, primary = p1.primary;
  for (const group of ["A", "B", "C", "D"]) $("p1" + group).textContent = fmt(p1.rates[group]);
  $("p1Scope").textContent = LANG === "en"
    ? `Means across ${p1.repeats} repeats on the same ${p1.initial_states} initial states`
    : `同一批${p1.initial_states}个初始状态，${p1.repeats}轮成功率均值`;
  $("p1Primary").textContent = LANG === "en"
    ? `Primary contrast with black images: live minus frozen state = ${primary.difference_pp.toFixed(1)} pp (95% paired bootstrap CI ${primary.ci95_lo.toFixed(1)}–${primary.ci95_hi.toFixed(1)} pp).`
    : `全黑条件主比较：实时−冻结首状态 = ${primary.difference_pp.toFixed(1)}个百分点（95%配对bootstrap区间 ${primary.ci95_lo.toFixed(1)}–${primary.ci95_hi.toFixed(1)}个百分点）。`;
  $("p1Coverage").textContent = LANG === "en"
    ? `${p1.formal_episodes} formal executions across four conditions; ${p1.smoke_episodes} engineering checks excluded. Repeats do not add independent initial states.`
    : `四条件共${p1.formal_episodes}次正式执行，${p1.smoke_episodes}次工程检查不进入统计；重复不增加独立初始状态。`;
  $("p2Finding").textContent = LANG === "en"
    ? `P2: ${p2.successes}/${p2.episodes} = ${fmt(p2.success_pc)} (95% stratified bootstrap CI ${p2.ci95_lo.toFixed(1)}–${p2.ci95_hi.toFixed(1)}%).`
    : `P2：${p2.successes}/${p2.episodes} = ${fmt(p2.success_pc)}（95%分层bootstrap区间 ${p2.ci95_lo.toFixed(1)}–${p2.ci95_hi.toFixed(1)}%）。`;
  $("p2Scope").textContent = LANG === "en"
    ? `Self-replay: ${p2.self_successes}/${p2.self_episodes}. ${p2.task_count} fixed tasks, ${p2.episodes / p2.task_count} selection-external target states per task.`
    : `自回放${p2.self_successes}/${p2.self_episodes}；固定${p2.task_count}个任务，每任务${p2.episodes / p2.task_count}个未参与动作选择的目标状态。`;
} else {
  const missing = LANG === "en" ? "Follow-up data could not be loaded; use the linked records." : "补充结果数据未加载，请查看所链接的记录。";
  $("p2Finding").textContent = missing;
  $("p1Scope").textContent = missing;
}
const replay = window.REPLAY_BASELINE;
if (replay) {
  const pc = (100 * replay.cross_ok / replay.cross_n).toFixed(1);
  $("replayFinding").textContent = LANG === "en"
    ? `Fixed actions succeed in ${replay.cross_ok}/${replay.cross_n} cross-replays (${pc}%). Self-replay: ${replay.self_ok}/${replay.self_n}.`
    : `固定动作交叉回放成功 ${replay.cross_ok}/${replay.cross_n}（${pc}%）；自回放为 ${replay.self_ok}/${replay.self_n}。`;
}
const toc = [...document.querySelectorAll(".contents a")];
const tocTargets = toc.map(a => document.querySelector(a.hash));
let tocScheduled = false;
function updateContents() {
  const mobile = matchMedia("(max-width: 800px)").matches;
  let active = toc[0];
  tocTargets.forEach((target, i) => {
    if (target && target.getBoundingClientRect().top <= (mobile ? 152 : 112)) active = toc[i];
  });
  if (mobile && active.classList.contains("sub")) active = toc.find(a => a.hash === "#vision");
  for (const a of toc) {
    if (a === active) a.setAttribute("aria-current", "location");
    else a.removeAttribute("aria-current");
  }
  tocScheduled = false;
}
addEventListener("scroll", () => { if (!tocScheduled) { tocScheduled = true; requestAnimationFrame(updateContents); } }, { passive: true });
addEventListener("resize", updateContents);
updateContents();

for (const region of document.querySelectorAll(".mx-wrap")) { region.tabIndex = 0; region.setAttribute("aria-label", LANG === "en" ? "Scrollable data table" : "可横向滚动的数据表"); }
for (const th of document.querySelectorAll("thead th")) th.scope = "col";
for (const th of document.querySelectorAll("tbody th.row:not([colspan])")) th.scope = "row";
