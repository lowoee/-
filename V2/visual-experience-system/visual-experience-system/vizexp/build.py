"""Deterministic conversion of reviewed skill cards and curated team decisions."""
from collections import Counter
from pathlib import Path
import re

from .common import ROOT, read_json, sha256, validate_schema, write_json


CATEGORIES = {
    "magnitude-selection": "magnitude",
    "ranking-selection": "ranking",
    "composition-selection": "composition",
    "distribution-selection": "distribution",
    "time-selection": "time",
    "correlation-selection": "correlation",
    "deviation-selection": "deviation",
    "flow-selection": "flow",
    "spatial-selection": "spatial",
}


def citation(sources, source_id, needle, interpretation=""):
    source = sources[source_id]
    text = source["_path"].read_text(encoding="utf-8-sig")
    if needle not in text:
        raise ValueError(f"Citation is absent in {source_id}: {needle[:70]}")
    start = text.index(needle)
    first = text[:start].count("\n") + 1
    return {
        "source_id": source_id,
        "start_line": first,
        "end_line": first + needle.count("\n"),
        "quote": needle,
        "interpretation": interpretation,
    }


def base_record(identifier, statement, category="general"):
    return {
        "id": identifier,
        "title": statement[:60],
        "statement": statement,
        "status": "active",
        "scope": {
            "organization": "any", "families": ["any"], "media": ["any"],
            "categories": [category], "conditions": [], "exceptions": [],
        },
        "check": {
            "question": "当前图表是否满足本条条件并存在可核对的违反证据？",
            "evidence_needed": ["chart.png", "brief.md", "data.csv", "图形规格或源码"],
            "pass_condition": "符合条件，或本条不适用；不为条目数量强行报错。",
            "fail_condition": "适用条件成立且图片或数据可定位具体违反证据。",
            "action": "根据实际表达目标提出与本条相符的修改，并说明缺失输入。",
        },
        "retrieval": {"keywords": [], "priority": 50},
        "validity": {"effective_from": None, "authority": "published_source"},
        "relations": {"overrides": [], "exceptions_to": [], "duplicates": []},
        "evidence": [],
        "provenance": {"method": "skill_conversion", "evaluation_dependent": False},
    }


def build(source_dir, output):
    source_dir = Path(source_dir).resolve()
    manifest = read_json(source_dir / "manifest.json")
    sources = {}
    for raw in manifest["sources"]:
        path = (source_dir / raw["path"]).resolve()
        if not path.is_relative_to(source_dir) or not path.is_file():
            raise ValueError(f"Invalid source path: {raw['path']}")
        if sha256(path) != raw["sha256"]:
            raise ValueError(f"Source changed, review and update manifest first: {raw['id']}")
        sources[raw["id"]] = {**raw, "_path": path}

    records = {}
    ft_lines = sources["ft-readme"]["_path"].read_text(encoding="utf-8").splitlines()
    for card in sorted((source_dir / "ft" / "capabilities").glob("*.md")):
        category = CATEGORIES.get(card.stem, "general")
        for line in card.read_text(encoding="utf-8-sig").splitlines():
            if not re.match(r"^\|p\d+\|", line):
                continue
            identifier, statement, location, limitation = line.strip("|").split("|", 3)
            if identifier in records:
                raise ValueError(f"Duplicate FT rule ID: {identifier}")
            number = int(re.search(r"L(\d+)", location)[1])
            quote = ft_lines[number - 1].strip()
            record = base_record(identifier, statement, category)
            record["scope"]["exceptions"] = [limitation]
            record["check"]["action"] = statement
            record["retrieval"]["keywords"] = [category, card.stem, statement]
            record["evidence"] = [citation(sources, "ft-readme", quote)]
            record["provenance"]["converted_from"] = "ft/capabilities/" + card.name
            records[identifier] = record

    # These records are reviewed abstractions of document decisions, not chart answers.
    for seed in read_json(source_dir / "curated.json")["experiences"]:
        record = base_record(seed["id"], seed["statement"], seed.get("category", "general"))
        record["status"] = seed.get("status", "active")
        record["scope"].update(seed.get("scope", {}))
        record["check"].update(seed.get("check", {}))
        record["retrieval"].update(seed.get("retrieval", {}))
        record["validity"].update(seed.get("validity", {}))
        record["relations"].update(seed.get("relations", {}))
        record["provenance"] = {
            "method": seed.get("method", "reviewed_distillation"),
            "evaluation_dependent": seed.get("evaluation_dependent", False),
        }
        record["evidence"] = [citation(sources, **item) for item in seed["citations"]]
        if record["provenance"]["evaluation_dependent"] and record["status"] == "active":
            raise ValueError("Evaluation-dependent rules cannot be active")
        if record["id"] in records:
            raise ValueError(f"Duplicate experience ID: {record['id']}")
        records[record["id"]] = record

    for record in records.values():
        validate_schema(record, "experience.schema.json")
        for field in ["overrides", "exceptions_to", "duplicates"]:
            for target in record["relations"][field]:
                if target not in records:
                    raise ValueError(f"Unresolved relation {record['id']} -> {target}")
                if field == "overrides" and records[target]["status"] == "active":
                    raise ValueError(f"Overridden rule must have an explicit inactive status: {target}")
        for evidence in record["evidence"]:
            if record["status"] == "active" and sources[evidence["source_id"]].get("evaluation_material"):
                raise ValueError("Evaluation answers cannot support active experiences")

    library = {
        "schema_version": 1,
        "library_id": "ft-team-visual-experiences-v1",
        "build_method": "确定性转换已验证skill条目，合并人工审阅的团队决议；构建时校验文件哈希、逐字引文、出处行号、关系与Schema。",
        "source_manifest": "sources/manifest.json",
        "experience_count": len(records),
        "status_counts": dict(Counter(r["status"] for r in records.values())),
        "experiences": sorted(records.values(), key=lambda r: r["id"]),
    }
    write_json(output, library)
    return library
