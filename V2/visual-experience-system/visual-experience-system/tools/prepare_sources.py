"""Prepare reviewed extraction seeds and source hashes from the bundled corpus."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "sources"


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


sources = []
for path in sorted(SOURCES.rglob("*")):
    if not path.is_file() or path.name in ["manifest.json", "curated.json"]:
        continue
    relative = path.relative_to(SOURCES).as_posix()
    if relative == "ft/README.md":
        identifier = "ft-readme"
    elif relative.startswith("ft/capabilities/"):
        identifier = "ft-card-" + path.stem
    elif relative.startswith("team/"):
        identifiers = {"信息图制作规范-v1": "team-v1", "信息图制作规范-v2": "team-v2",
                       "群聊决议摘录": "team-decisions", "评审意见摘录": "team-reviews",
                       "模板代码摘录": "team-template", "README": "team-readme"}
        identifier = identifiers[path.stem]
    else:
        identifier = "archive-" + path.stem
    item = {"id": identifier, "path": relative, "title": path.stem,
            "kind": "team_document" if relative.startswith("team/") else "reference_document",
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "evaluation_material": relative.startswith("historical-review/"),
            "limitations": "经验用途与出处分别核对；复制文件不等于已证明方法普适有效。"}
    if relative == "ft/README.md":
        item.update({"url": "https://github.com/Financial-Times/chart-doctor/blob/befb9cba21849432a4029d0cfdda938819ae733f/visual-vocabulary/README.md",
                     "revision": "befb9cba21849432a4029d0cfdda938819ae733f",
                     "license_note": "仓库根有MIT声明，Visual Vocabulary README另有FT保留版权声明；公开再分发前核对适用范围。"})
    sources.append(item)

experiences = []


def add(identifier, statement, quote, source="team-v2", *, status="active", media=None,
        overrides=None, exceptions_to=None, conditions=None, date="2026-06-18",
        authority="published_team_standard", method="reviewed_distillation", evaluation=False):
    experiences.append({
        "id": identifier, "statement": statement, "status": status,
        "scope": {"organization": "team-finance", "families": ["infographic"],
                  "media": media or ["any"], "conditions": conditions or [], "exceptions": []},
        "check": {"question": "当前图是否在适用范围内违反本条约定？",
                  "action": statement},
        "validity": {"effective_from": date, "authority": authority},
        "relations": {"overrides": overrides or [], "exceptions_to": exceptions_to or []},
        "retrieval": {"priority": 100 if authority == "explicit_team_decision" else 80,
                      "keywords": [identifier, statement]},
        "method": method, "evaluation_dependent": evaluation,
        "citations": [{"source_id": source, "needle": quote}],
    })


# Supersession records are retained for audit but are never retrieved as advice.
for identifier, statement, quote in [
    ("team-v1-1.3", "旧版推荐小标题使用主题与结论格式。", "小标题推荐使用“主题｜结论”的格式"),
    ("team-v1-1.4", "旧版脚注间距40px。", "图表区与脚注之间保留 40px 间距"),
    ("team-v1-2.2", "旧版要求非零折线轴保留0刻度和断轴符号。", "此时必须在纵轴底部保留 0 刻度，并画上断轴符号"),
    ("team-v1-3.1", "旧版金额保留两位小数，后续新增同类统一要求。", "金额保留两位小数。"),
    ("team-v1-3.2", "旧版数据标注写全单位。", "数据标注写全单位"),
]:
    add(identifier, statement, quote, "team-v1", status="superseded", date="2025-03-10")

for identifier, statement, quote, conditions in [
    ("team-v1-1.1", "手机卡片宽375，左右内边距16。", "手机端卡片宽度 375，左右内边距 16。", []),
    ("team-v1-1.2", "主标题不超过两行，用一句话呈现结论，可用品牌紫突出关键词。", "主标题不超过两行，用一句话写出结论，关键词可以用品牌紫高亮。", []),
    ("team-v1-2.1", "柱状图数值轴从0开始。", "柱状图的纵轴必须从 0 开始。", ["柱状图"]),
    ("team-v1-4.1", "主色品牌紫#7B3FE4，辅助色蓝#3E7BFA与浅紫#B9A3F0。", "主色为品牌紫 `#7B3FE4`，辅助色为蓝 `#3E7BFA` 和浅紫 `#B9A3F0`。", []),
    ("team-v1-5.1", "脚注应写明数据来源。", "脚注写明数据来源。", []),
]:
    add(identifier, statement, quote, "team-v1", media=["mobile"] if identifier.endswith(("1.1", "1.2")) else None,
        conditions=conditions, date="2025-03-10")

width_rule = next(r for r in experiences if r["id"] == "team-v1-1.1")
width_rule["scope"]["conditions"] = ["先确认规范所指的外层卡片与源码测量对象一致，核对渲染倍率和单位。"]
width_rule["scope"]["exceptions"] = ["外层画布已符合名义宽度，仅内层面板因装饰外边距变窄时，若没有依据确认规范指内层面板，作为口径疑问保留，不判为尺寸错误。"]
width_rule["check"]["fail_condition"] = "能确认实际测量的是规范要求的同一层容器，且单位换算后确有差异。"
width_rule["citations"][0]["interpretation"] = "条款给出尺寸，未区分画布和装饰内框；测量对象一致性由审查契约补充。"

add("team-v2-1.3", "手机端小标题只写主题，结论放主标题。", "小标题只写主题，不再加“｜结论”。结论放在主标题里。", media=["mobile"], overrides=["team-v1-1.3"])
add("team-v2-1.4", "图表区底部到脚注分隔线间距为24px。", "图表区底部到脚注分隔线的间距改为 24px。", overrides=["team-v1-1.4"])
add("team-v2-3.1", "金额保留两位小数，同类数值的小数位一致。", "金额保留两位小数。同一张图中，同一类数值（例如所有数据标注）的小数位数必须一致。", overrides=["team-v1-3.1"])
add("team-v2-3.2", "数据标注只写数值，单位含百分号统一放单位行。", "数据标注只写数值，不带单位（包括 %）。单位统一写在单位行里。", overrides=["team-v1-3.2"])
add("team-v2-2.4", "单位行左边缘与纵轴刻度数字最左侧对齐。", "单位行的左边缘与纵轴刻度数字的最左侧对齐，不要居中放在轴线上方。")
add("team-v2-2.5", "量级相差5倍以上的指标拆成上下两图，团队不用双纵轴。", "量级相差 5 倍以上的指标不放在同一个纵轴上，拆成上下两张图。不使用双纵轴。", conditions=["不同指标量级相差超过5倍"])
add("team-v2-4.3", "最多1主色加2辅助色，涨跌色另计；表格用中性底色，最多高亮1至2关键行。", "一张图最多使用 1 个主色和 2 个辅助色，涨跌色不计入。表格行使用中性底色，最多只对 1–2 个关键行高亮。")
add("team-v2-5.2", "来源行写对外提供方与报告名称，隐藏内部字段。", "来源行只写对外的数据提供方和报告名称，不能出现 source_id、“用户提供数据”之类的内部字段。")
add("team-v2-6.1", "手机类目在词边界换行，或使用规范附录中的简称。", "手机端的类目标签不能在一个词的中间断行。", media=["mobile"])
add("team-chat-20260702", "面向该团队国内投资者时，各市场统一红涨绿跌。", "统一红涨绿跌，不分市场。", "team-decisions", date="2026-07-02", authority="explicit_team_decision")
add("team-chat-20260814", "折线轴非零起点时，不画断轴符号，也不画孤立0刻度。", "折线图纵轴不从 0 开始时，不画断轴符号，也不画 0 刻度。规范 v1 的 2.2 作废", "team-decisions", overrides=["team-v1-2.2"], conditions=["折线图且纵轴不从0开始"], date="2026-08-14", authority="explicit_team_decision")
add("team-chat-20260903", "PC大屏小标题可保留主题与结论格式。", "PC 大屏看板空间足够，小标题可以保留“主题｜结论”的格式。手机端仍然按 v2 的 1.3 执行。", "team-decisions", media=["large_screen"], exceptions_to=["team-v2-1.3"], date="2026-09-03", authority="explicit_team_decision")
add("team-chat-20260920", "保留品牌紫，个人配色偏好不作为审查修改依据。", "品牌主色不改。个人审美偏好不进规范，评审时也不作为修改意见。", "team-decisions", date="2026-09-20", authority="explicit_team_decision")
add("team-proposal-remove-labels", "提案主张删除所有数据标注，但该提案已被明确否决。", "不采纳。普通用户主要看标注读数。", "team-decisions", status="rejected", date="2026-10-11", authority="rejected_proposal")
add("team-template-footer", "旧模板常量FOOTER_GAP仍为40，附TODO待按v2更新。", "export const FOOTER_GAP = 40; // TODO: 规范 v2 要改，等定稿后同步", "team-template", status="reference_only", date="2026-05-30", authority="implementation_snapshot")
add("team-template-labels", "模板仍带单位与断轴设置，需按后续规范决议审查。", "export const LABEL_WITH_UNIT = true;", "team-template", status="reference_only", date="2026-05-30", authority="implementation_snapshot")

unit = {
    "id": "ft-contract-units", "statement": "核对字段类型、单位和口径，缺少单位时先确认，不能自行猜测。",
    "scope": {"organization": "any", "families": ["any"]},
    "method": "reviewer_authored_contract",
    "citations": [{"source_id": "ft-card-magnitude-selection", "needle": "数据类型、单位、范围和语义须显式核对。"}],
    "retrieval": {"priority": 90, "keywords": ["单位", "口径", "unit"]},
}
experiences.append(unit)
for identifier, title, quote in [
    ("pending-p24", "累积曲线不均衡计算定义待核查。", "A good way of showing how unequal a distribution is"),
    ("pending-p35", "地震波形图的具体视觉编码待核查。", "Another alternative to the circle timeline"),
    ("pending-p38", "比例堆叠同时编码总量与比例的具体方式待核查。", "A good way of showing the size and proportion of data at the same time"),
]:
    experiences.append({"id": identifier, "statement": title, "status": "needs_review",
                        "citations": [{"source_id": "ft-readme", "needle": quote}],
                        "scope": {"organization": "any", "families": ["any"]}})

save(SOURCES / "manifest.json", {"schema_version": 1, "sources": sources})
save(SOURCES / "curated.json", {"schema_version": 1, "method": "人工审阅的转换种子；更改需要核对原文与适用条件。", "experiences": experiences})
print(f"Prepared {len(sources)} sources and {len(experiences)} curated records")
