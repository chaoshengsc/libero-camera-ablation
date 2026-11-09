"""Render bilingual method/layout diagrams for direct repository review; no policy execution."""

from html import escape
from pathlib import Path

FONT = "-apple-system,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif"


def canvas(width, height, heading, content):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">\n'
        f'<title>{escape(heading)}</title>\n<rect width="100%" height="100%" fill="white"/>\n'
        f"<style>text{{font-family:{FONT};font-size:14px;fill:#253244}}.muted{{fill:#667085;font-size:12px}}</style>\n"
        f'<text x="22" y="30" style="font-size:19px;font-weight:650">{escape(heading)}</text>\n' + "\n".join(content) + "\n</svg>\n"
    )


def flow(cn):
    heading = "π0／π0.5的评测形成观测—动作闭环" if cn else "π0/π0.5 evaluation forms an observation–action loop"
    boxes = [
        (22, 188, ["当前观测", "主视角＋腕部图像", "机械臂状态＋任务指令"] if cn else ["Current observation", "Agent + wrist images", "Robot state + instruction"]),
        (236, 190, ["指定相机干预", "仅改目标图像／掩码", "其余输入正常传入"] if cn else ["Targeted intervention", "Target image / visual mask", "Other inputs remain live"]),
        (452, 166, ["公开策略检查点", "预测一个动作块", "模型未重新训练"] if cn else ["Public policy checkpoint", "Predict an action chunk", "No retraining in this study"]),
        (
            644,
            234,
            ["执行部分预测动作", "环境产生下一次观测", "再次查询策略"] if cn else ["Execute part of the chunk", "Observe the updated environment", "Query the policy again"],
        ),
    ]
    out = []
    for x, width, lines in boxes:
        out.append(f'<rect x="{x}" y="62" width="{width}" height="112" rx="5" fill="#f5f7fa" stroke="#d5dce5"/>')
        for i, line in enumerate(lines):
            style = ' style="font-weight:650"' if i == 0 else ' class="muted"'
            out.append(f'<text x="{x + width / 2}" y="{91 + i * 27}" text-anchor="middle"{style}>{escape(line)}</text>')
    for a, b in [(210, 236), (426, 452), (618, 644)]:
        out.append(f'<path d="M{a + 4} 117H{b - 6}m-6 -5 6 5-6 5" fill="none" stroke="#526f91" stroke-width="1.6"/>')
    out.append('<path d="M762 180V213H116V180m-5 7 5-7 5 7" fill="none" stroke="#526f91" stroke-width="1.6"/>')
    label = "新一轮图像与状态随环境正常更新；同初态不代表后续输入逐位相同" if cn else "Images/state update with the environment; matched starts do not imply identical later inputs"
    out.append(f'<text x="440" y="204" text-anchor="middle" class="muted">{label}</text>')
    notes = (
        ["π0：预测50步，执行5步后重观察；π0.5：预测50步，执行10步后重观察。", "OpenVLA另用主视角＋指令与单步动作，不套用图中的双视角／状态输入配置。"]
        if cn
        else [
            "π0: predict 50 actions, execute 5 before observing again; π0.5: predict 50, execute 10.",
            "OpenVLA instead uses agent view + instruction and single-step actions, outside the dual-view/state path.",
        ]
    )
    for i, note in enumerate(notes):
        out.append(f'<text x="22" y="{247 + i * 24}" class="muted">{escape(note)}</text>')
    return canvas(900, 294, heading, out)


def slots(cn):
    heading = "保留原槽位可避免把腕部图像误放进主视角槽" if cn else "Preserving camera slots prevents wrist images entering the agent-view slot"
    headers = ["槽位0 · 主视角", "槽位1 · 腕部", "槽位2 · 原空槽"] if cn else ["Slot 0 · agent", "Slot 1 · wrist", "Slot 2 · reserved empty"]
    labels = ["正常输入", "主视角缺失 · 旧实现", "主视角缺失 · 修复后"] if cn else ["Normal input", "Agent missing · before", "Agent missing · after"]
    values = (
        [["主视角", "腕部", "空"], ["腕部（错位）", "空", "空"], ["空", "腕部（原位）", "空"]]
        if cn
        else [["Agent image", "Wrist image", "Empty"], ["Wrist image (shifted)", "Empty", "Empty"], ["Empty", "Wrist image (in place)", "Empty"]]
    )
    out = []
    for j, label in enumerate(headers):
        out.append(f'<text x="{300 + j * 215}" y="68" text-anchor="middle" class="muted">{escape(label)}</text>')
    for i, (label, row) in enumerate(zip(labels, values, strict=True)):
        y = 86 + i * 58
        out.append(f'<text x="22" y="{y + 27}">{escape(label)}</text>')
        for j, value in enumerate(row):
            bad, good = i == 1 and j == 0, i == 2 and j == 1
            color, stroke = ("#fff0eb", "#c86a4b") if bad else (("#edf4fb", "#547da6") if good else ("#f6f7f9", "#d5dce5"))
            out.append(f'<rect x="{202 + j * 215}" y="{y}" width="196" height="40" rx="4" fill="{color}" stroke="{stroke}"/>')
            out.append(f'<text x="{300 + j * 215}" y="{y + 26}" text-anchor="middle">{escape(value)}</text>')
    note = (
        "示例采用π0.5 v044三槽配置；六策略修复分别保留各自原有占位和空相机预算规则。"
        if cn
        else "Example: π0.5 v044 three-slot layout. The six-policy fix preserves each policy’s placeholder and empty-camera contract."
    )
    out.append(f'<text x="22" y="280" class="muted">{escape(note)}</text>')
    return canvas(900, 304, heading, out)


def build_presentation_figures(root):
    for cn, folder in [(False, root / "media"), (True, root / "media/zh")]:
        (folder / "evaluation_loop.svg").write_text(flow(cn))
        (folder / "camera_slot_fix.svg").write_text(slots(cn))


if __name__ == "__main__":
    build_presentation_figures(Path(__file__).resolve().parents[2])
