from pathlib import Path
import csv
import io
import json
import re


MAX_TEXT_BYTES = 4 * 1024 * 1024


def read_text(path):
    path = Path(path)
    if path.stat().st_size > MAX_TEXT_BYTES:
        raise ValueError(f"Text input exceeds {MAX_TEXT_BYTES} bytes: {path.name}")
    return path.read_text(encoding="utf-8-sig")


def discover(root):
    root = Path(root).resolve()
    if (root / "chart.png").is_file():
        return [root]
    charts = sorted(p for p in root.iterdir() if p.is_dir() and (p / "chart.png").is_file())
    if not charts:
        raise ValueError("No chart.png found in the directory or its immediate child directories")
    return charts


def load_chart(path, organization="auto"):
    path = Path(path).resolve()
    image = path / "chart.png"
    if not image.is_file():
        raise ValueError(f"Missing chart.png: {path}")
    brief = read_text(path / "brief.md") if (path / "brief.md").exists() else ""
    rows = []
    if (path / "data.csv").exists():
        rows = list(csv.DictReader(io.StringIO(read_text(path / "data.csv"))))
    spec = json.loads(read_text(path / "spec.vl.json")) if (path / "spec.vl.json").exists() else None
    html = read_text(path / "source.html") if (path / "source.html").exists() else None
    family = "infographic" if html is not None else ("statistical" if spec is not None else "unknown")
    media = "unknown"
    if re.search(r"手机|移动端|375\s*(?:pt|px)", brief):
        media = "mobile"
    elif "大屏" in brief:
        media = "large_screen"
    elif re.search(r"PC|PDF|桌面", brief, re.I):
        media = "desktop"
    if organization == "auto":
        organization = "team-finance" if family == "infographic" and (
            (path.parent / "团队资料包").is_dir() or "团队规范：team-finance" in brief
        ) else "unknown"
    return {
        "chart_id": path.name, "path": str(path), "image": str(image),
        "brief": brief, "data": rows, "spec": spec, "html": html,
        "family": family, "media": media, "organization": organization,
    }


def categories(chart):
    # Structural routing is independent of filenames, reference answers and chart IDs.
    text = chart["brief"] + json.dumps(chart["spec"], ensure_ascii=False) + (chart["html"] or "")
    result = {"magnitude"}
    signals = {
        "composition": r"arc|pie|treemap|组成|构成|多选|占比",
        "time": r'"temporal"|line-chart|走势|趋势|周度|日线|季度|年度',
        "correlation": r"scatter|bubble|heatmap|\"rect\"|independent|关系|相关",
        "ranking": r"排名|比较|排行|渠道|行业|hbar",
        "distribution": r"boxplot|violin|分布|直方|箱线|频数",
        "spatial": r"geoshape|经度|纬度|地图|choropleth",
        "flow": r"waterfall|sankey|瀑布|利润桥|流动|来源去向",
        "deviation": r"偏差|达标|反对|中立|赞同|diverging",
    }
    result.update(category for category, pattern in signals.items() if re.search(pattern, text, re.I))
    return result
