const R = window.RESULTS || [];
const $ = (id) => document.getElementById(id);
const fmt = (x) => x == null ? "—" : x.toFixed(1) + "%";
const sum = (a) => a.reduce((p, q) => p + q, 0);

// ---- 语言：默认跟随浏览器，？lang=zh|en 或右上角按钮切换。英文版在渲染后按词典替换文本（整句在前，短词在后）。
const LANG = new URLSearchParams(location.search).get("lang") || ((navigator.language || "").toLowerCase().startsWith("zh") ? "zh" : "en");
const DICT = [
  ["已完成补充实验：状态更新与选择外固定动作回放", "Completed follow-ups: state updates and selection-external replay"],
  ["完整实验与P1/P2", "Full experiments and P1/P2"],
  ["选择外固定动作回放、状态更新与解释边界", "Selection-external replay, state updates and interpretation limits"],
  ["此图保留早期选择集上的交叉回放；已完成的选择外回放和状态更新检查见下方完整实验入口。", "This figure retains earlier selection-set cross-replay; completed selection-external replay and state-update checks are in the full experiment report below."],
  ["机器人策略真的在看画面吗？", "Do robot policies actually use their cameras?"],
  ["LIBERO-Spatial 上四种机器人策略的相机消融实验", "Camera ablations of four robot policies on LIBERO-Spatial"],
  ["同一任务：π0.5 正常成功、涂黑失败，LeRobot π0 涂黑仍成功", "Same task: π0.5 succeeds with vision and fails with black input; LeRobot π0 still succeeds with black input"],
  ["同一任务、同一初始状态。右侧两次运行中，策略收到的是黑图。", "Same task and initial state. In the two right-hand runs, the policy receives black images."],
  ["开环回放：固定动作能完成多少任务", "Open-loop replay: how far fixed actions go"],
  ["动作来自官方 π0 正常运行。每任务事后挑出的最好一套为 77.8%，存在选择偏差，不能当作无偏基线。回放不说明 LeRobot π0 看不见时实际在做什么。", "Actions come from official π0 with normal vision. The post-hoc best sequence per task scores 77.8%, but selection makes it an optimistic estimate, not an unbiased baseline. Replay does not identify what blind LeRobot π0 actually does."],
  ["复现图使用正态近似区间；官方 π0 对照使用 Wilson 区间。重复运行与配对比较的限制见实验记录。", "Reproduction uses normal-approximation intervals; the official π0 control uses Wilson intervals. See the notes for repeat and paired-comparison limitations."],
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
  ["四个策略里有三个离开实时相机画面就无法完成任务；一个公开的 π0 权重在所有相机涂黑后仍有 53–56% 的成功率。做消融之前，先复现了五个公开权重。", "Three of the four policies fail without a live camera image. One public π0 checkpoint still succeeds 53–56% of the time with every camera blacked out. Five public checkpoints were reproduced first."],
  ["每个模型评测 500 回合，与原作者公布的基准对比。两个 95% 置信区间有重叠即算复现。", "Each model is evaluated for 500 episodes and compared with the reference published by its authors. A result counts as reproduced when the two 95% confidence intervals overlap."],
  ["SmolVLA 用的是只在 LIBERO-Spatial 上训练的公开权重，评测时 n_action_steps=10。点击模型行可以核对基准出处与原始评测。", "SmolVLA uses a public checkpoint trained on LIBERO-Spatial only, evaluated with n_action_steps=10. Select a model row to inspect reference sources and raw evaluations."],
  ["本节的 π0 是 LeRobot 的公开权重，500 回合的正常成功率是 73%。官方 π0 在 OpenPI 原版管线下去掉视觉后是 0%（1.5 节），所以下面的现象只说明这个权重（连同它的推理管线），不代表所有 π0。", "π0 in this section is LeRobot's public checkpoint, which scores 73% over 500 normal episodes. Official π0 in OpenPI's own pipeline scores 0% without vision (section 1.5), so the behaviour below describes this checkpoint (together with its inference pipeline), not π0 in general."],
  ["每格是该任务 50 回合的成功率（%）。列标题是“拿起黑碗并放到盘子上”里碗的初始位置。", "Each cell is the success rate (%) over 50 episodes of that task. Column headers give where the bowl starts in \"pick up the black bowl and place it on the plate\"."],
  ["相机消融只改变画面输入；OpenVLA只接收主视角和指令，其余三个检查点还接收腕部画面与状态。", "Camera ablations alter image inputs. OpenVLA uses the agent view and instruction; the other three checkpoints also receive wrist images and state."],
  ["早期相机消融每次100回合，按相同初始状态比较。区间取决于配对与重复结构，不设统一的13点阈值；π0早期同条件重复最多相差18点。", "Earlier camera runs use 100 matched initial states. Uncertainty depends on pairing and repeats, not a universal 13-point threshold; earlier pi0 repeats differed by up to18 points."],
  ["三个检查点在所测全黑回合中均未成功完成任务；LeRobot π0 v044仍有一半以上成功。", "Three checkpoints completed no tested all-black episode; LeRobot pi0 v044 still succeeded in more than half."],
  ["π0 各任务的成功次数（每个任务 10 回合）：全涂黑后的失败集中在三个任务上。", "π0 successes per task (10 episodes each): the failures with black cameras are concentrated in three tasks."],
  ["π0.5 和 SmolVLA 需要实时画面；对 π0，只有两路相机都涂黑才有稳定的影响。", "π0.5 and SmolVLA need a live image. For π0, only blacking out both cameras has a reliable effect."],
  ["每格是 100 回合里的成功次数，每个条件跑了两次（同样的脚本、同一个种子）。噪声是标准差 0.1 的高斯噪声；冻结首帧持续使用真实旧图像，也改变图像—状态同步，不能称整体分布内干预。对 π0.5 和 SmolVLA，腕部相机比主视角更重要。π0 的单路相机、噪声、冻结条件两次相差 9 到 18，说明不了它依赖哪一路相机。只涂黑腕部相机又跑了三次，是 72、67 和 70。", "Each cell is successes out of 100 episodes; every condition was run twice with the same scripts and seed. Noise is Gaussian with standard deviation 0.1. Freezing repeats a real first-frame image but also changes image–state synchronization; it is not guaranteed to remain in-distribution. For π0.5 and SmolVLA the wrist camera matters more than the agent view. π0's single-camera, noise and frozen-image runs differ by 9 to 18 between the two runs, so they cannot show which camera it depends on. Three more runs with the wrist camera black gave 72, 67 and 70."],
  ["在全涂黑仍能成功的任务上，它的路线和看得见时在噪声内无法区分；在从未成功的任务 7 上，它走到了别处。两次运行都是这样。", "On the tasks it still solves blind, its path cannot be told apart from the sighted path within noise. On task 7, where it never succeeds, it goes somewhere else. Both runs agree."],
  ["各任务的末端路线差异（cm，动态时间规整后的平均点距）。整套比较跑了两次；标出的是全涂黑后成功不到一半的任务。", "End-effector path difference per task (cm, mean point distance after dynamic time warping). The whole comparison was run twice; tasks where blind π0 succeeds less than half the time are highlighted."],
  ["两次正常运行几乎重合的任务（第 1 次的任务 0–3，第 2 次的任务 0）是同一个种子下还没有分叉，不能反映噪声；其余任务上的噪声底线平均是 3.4 和 3.3 cm。全涂黑仍能成功的任务上，路线相差 2.8 和 3.2 cm。任务 9 第 1 次相差 7.8 cm，第 2 次只有 4.9 cm，不如任务 7 清楚。这种比较分不出策略是跟着碗走，还是每个任务重复一套动作；后续已测量场景变化并做开环回放，见仓库 README 第 1.5 节。", "Tasks where the two sighted runs are almost identical (tasks 0–3 in run 1, task 0 in run 2) use the same seed and had not yet diverged, so they say nothing about noise; on the other tasks the noise floor averages 3.4 and 3.3 cm. On the tasks blind π0 still solves, the path differs by 2.8 and 3.2 cm. Task 9 differs by 7.8 cm in run 1 but only 4.9 cm in run 2, so it is less clear than task 7. This comparison cannot separate a policy that tracks the bowl from one that repeats one motion per task, the subsequent scene-variation measurement and open-loop replay are in repository README section 1.5."],
  ["每个任务一段成功、一段失败的录像。全涂黑的录像是环境的真实渲染，模型当时收到的是黑图。", "One successful and one failed episode per task. Recordings of the all-black runs show the simulator's real rendering; the model received black images."],
  ["回放视频体积大，没有随仓库发布。在本地把评测输出的 videos/ 放到 dashboard/data/<run>/ 下，就能在这里播放。", "Replay videos are too large to publish with the repository. Put each run's videos/ folder under dashboard/data/<run>/ locally to play them here."],
  ["置信区间为二项分布的正态近似。全部数据、脚本与说明见 GitHub 仓库。", "Confidence intervals use the normal approximation to the binomial. All data, scripts and notes are in the GitHub repository."],
  ["公开权重复现到基准的误差范围内", "public checkpoints reproduced within sampling error"],
  ["π0 在相机全涂黑后的成功率", "π0 success rate with every camera black"],
  ["π0.5 画面冻结后的成功率", "π0.5 success rate with the image frozen"],
  ["整个回合只给第一帧画面（%），各 100 回合", "first frame only for the whole episode (%), 100 episodes each"],
  ["降到 0%：", "Drop to 0%: "],
  ["SmolVLA 论文 Table 2（每任务 10 次）；该权重只在 LIBERO-Spatial 上训练，评测用 n_action_steps=10", "SmolVLA paper, Table 2 (10 episodes per task); this checkpoint was trained on LIBERO-Spatial only and is evaluated with n_action_steps=10"],
  ["OpenPI LIBERO README（LeRobot 文档复现为 97.0%）", "OpenPI LIBERO README (the LeRobot docs report 97.0%)"],
  ["openvla README（3 种子 × 500 回合，A100）", "openvla README (3 seeds × 500 episodes, A100)"],
  ["LeRobot 模型卡（500 回合；原版 DP 仓库同等模型 64.2%）", "LeRobot model card (500 episodes; the equivalent model in the original DP repo scores 64.2%)"],
  ["HF 仓库自带 eval_info.json（500 回合）", "eval_info.json shipped in the HF repo (500 episodes)"],
  ["π0.5对腕部涂黑、屏蔽和冻结均高度敏感；LeRobot π0 v044的变化落在预设等效范围内。", "Pi0.5 is highly sensitive to wrist black/masked/frozen input; LeRobot pi0 v044 changes stay within the prespecified margin."],
  ["每个条件 500 回合（10 个任务 × 50 个初始状态，各条件初始状态相同；π0.5 腕部涂黑一项是同一组 100 个初始状态跑 5 次）。“屏蔽”指在模型内部把这一路相机的槽位换成空相机占位、掩码置 0；“冻结”指整个回合只给第一帧的真实画面。π0 与双相机按初始状态配对，各条件差值的 95% 区间都在预设的 ±8 个百分点以内。逐回合结果见仓库的 results/single_camera.csv。", "500 episodes per condition (10 tasks × 50 initial states, the same initial states for every condition; π0.5 wrist black is the same 100 initial states run 5 times). \"Dropped\" fills the camera's slot inside the model with the empty-camera placeholder and sets its mask to 0; \"frozen\" gives the real first-frame image for the whole episode. Paired by initial state against both cameras, every π0 difference has a 95% interval inside the pre-set ±8-point margin. Per-episode results are in results/single_camera.csv in the repository."],
  ["官方 π0 离开视觉就不能完成任务，只屏蔽腕部也是 0%；只屏蔽主视角还剩 77%。看不见也能成功的只有 LeRobot 这个权重。", "Official π0 cannot do the tasks without vision, and scores 0% with only the wrist camera masked; with only the main view masked it keeps 77%. Only LeRobot's checkpoint succeeds without vision."],
  ["官方 π0 为 Physical Intelligence 的 pi0_libero 检查点，在 OpenPI 原版管线下运行（渲染 256），正常 500 回合 96.4%，初始状态与 1.4 节逐回合相同；去视觉的各条件 100 回合。LeRobot π0 在 LeRobot 管线下运行（渲染 360）；官方 π0 改用 360 渲染复测，正常 99/100，去视觉仍为 0/100，分辨率不是原因。两边管线不同，差别不能单独归因到权重。LeRobot 转换版的官方权重在 LeRobot 管线下 0/50，没能跑通。设计与判读规则在运行前写好，见仓库 docs/NOTES_CN.md；汇总在 results/official_pi0_summary.csv。", "Official π0 is Physical Intelligence's pi0_libero checkpoint, run in OpenPI's own pipeline (256 rendering): 96.4% over 500 normal episodes, with initial states identical episode by episode to section 1.4; 100 episodes per vision-removal condition. LeRobot π0 runs in the LeRobot pipeline (360 rendering); official π0 re-run at 360 scores 99/100 normally and still 0/100 without vision, so resolution is not the cause. The pipelines differ, so the difference cannot be attributed to the weights alone. The LeRobot conversion of the official checkpoint scored 0/50 in the LeRobot pipeline and did not run. The design and reading rule were written before running, see docs/NOTES.md in the repository; the summary is in results/official_pi0_summary.csv."],
  ["官方 π0 与 LeRobot π0 去掉相机后的成功率", "Official π0 vs. LeRobot π0 with cameras removed"],
  ["官方 π0 对照", "Official π0 control"],
  ["去掉腕部相机：每个条件 500 回合", "Wrist camera removed: 500 episodes per condition"],
  ["测试时去掉一路相机后的成功率", "Success rate with one camera removed at test time"],
  ["策略的输入，以及各实验改了哪一项", "What the policy receives and what each experiment changes"],
  ["π0 有无相机输入时的末端路线", "End-effector paths of π0 with and without camera input"],
  ["正常与全涂黑成功率对比", "Normal vs. all-black success rate"], ["各模型成功率对比", "Success rate by model"],
  ["四个机器人策略在 LIBERO-Spatial 上的相机输入消融", "Camera-input ablations of four robot policies on LIBERO-Spatial"],
  ["LIBERO-Spatial 各任务成功率", "LIBERO-Spatial success rate per task"],
  ["看不见的 π0 在成功的任务上走的是同一条路线", "Where blind π0 succeeds, it follows the sighted path"],
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
for (const [id, name] of [["figInputs", "inputs"], ["figTraj", "trajectory"], ["figSingle", "single_camera"], ["figOfficial", "official_pi0"], ["figReplay", "open_loop_replay"]]) {
  $(id).onerror = () => $(id).closest(".fig").classList.add("hidden");
  $(id).src = `../media/${LANG === "en" ? "" : "zh/"}${name}.svg?v=layout-4`;
}
$("figInputsMobile").srcset = `../media/${LANG === "en" ? "" : "zh/"}inputs-mobile.svg?v=layout-4`;
if (LANG === "en") {
  document.documentElement.lang = "en"; document.title = trStr(document.title);
  new MutationObserver(ms => ms.forEach(m => m.type === "characterData" ? trNode(m.target) : m.addedNodes.forEach(trNode)))
    .observe(document.body, { childList: true, subtree: true, characterData: true });
  trNode(document.body);
}

const done = R.filter(r => r.status === "done");
// 复现判定：本仓库 95% 区间与基准区间（± 或其 95% CI，没有则视为一个点）有重叠
const reproduced = (r) => { const b = r.baseline_pm ?? r.baseline_ci ?? 0; return Math.abs(r.pc - r.baseline_pc) <= r.ci + b; };
const BO = window.BLACKOUT || { summary: [], runs: [] };
const FU = window.FOLLOWUP || {};
const MNAME = { pi0: "π0", "pi0.5": "π0.5" };

// ---- 三条结论（数字全部取自数据）
{
  const ok = done.filter(reproduced), p0 = BO.summary.find(r => r.model === "pi0"), p5 = (FU.perturb || []).find(r => r.model === "pi0.5");
  const zero = BO.summary.filter(r => sum(r.black) === 0).map(r => MNAME[r.model] || r.model);
  $("keys").innerHTML = [
    [`${Math.min(...FU.pi0_black_runs)}–${Math.max(...FU.pi0_black_runs)}%`, "π0 在相机全涂黑后的成功率", "降到 0%：" + zero.join(" · ")],
    [`${p5.normal} → ${p5.freeze}`, "π0.5 画面冻结后的成功率", "整个回合只给第一帧画面（%），各 100 回合"],
    [`${ok.length} / ${done.length}`, "公开权重复现到基准的误差范围内", done.map(r => r.model).join(" · ")],
  ].map(([v, k, d], i) => `<a class="key" href="${["#blackout", "#perturbations", "#repro"][i]}"><span class="v">${v}</span><span class="key-copy"><span class="k">${k}</span><span class="d">${d}</span></span><svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m9 5 7 7-7 7"/></svg></a>`).join("");
}

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
  const cols = [["normal", "正常"], ["noise", "加高斯噪声"], ["freeze", "冻结首帧"], ["agent_black", "只涂主视角"], ["wrist_black", "只涂腕部"], ["all_black", "全涂黑"]];
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

drawChart(); selectModel(selectedModel); drawMatrix(); drawBlackout(); drawFollowup();
addEventListener("resize", () => { drawChart(); drawBlackout(); });

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
for (const link of document.querySelectorAll("[data-doc]")) link.href = `https://github.com/chaoshengsc/libero-camera-ablation/blob/main/${link.dataset.doc}${LANG === "en" ? "" : "_CN"}.md`;
for (const link of document.querySelectorAll("[data-figure]")) link.href = `../media/${LANG === "en" ? "" : "zh/"}${link.dataset.figure}.svg`;
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
