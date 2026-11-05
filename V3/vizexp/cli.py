import argparse
import json
from pathlib import Path
import sys
import time

from .agent import isolated_profile, make_prompt, review_chart
from .build import build
from .charts import discover, load_chart
from .common import ROOT, read_json, validate_schema, write_json
from .retrieval import retrieve


def parser():
    result = argparse.ArgumentParser(description="可追溯经验库构建与图表审查")
    sub = result.add_subparsers(dest="command", required=True)
    builder = sub.add_parser("build")
    builder.add_argument("--sources", type=Path, default=ROOT / "sources")
    builder.add_argument("--output", type=Path, default=ROOT / "knowledge/experiences.json")
    validator = sub.add_parser("validate")
    validator.add_argument("--kb", type=Path, default=ROOT / "knowledge/experiences.json")
    for name in ["retrieve", "review"]:
        command = sub.add_parser(name)
        command.add_argument("input", type=Path)
        command.add_argument("--kb", type=Path, default=ROOT / "knowledge/experiences.json")
        command.add_argument("--output", type=Path, required=True)
        command.add_argument("--organization", choices=["auto", "team-finance", "unknown"], default="auto")
        if name == "review":
            command.add_argument("--codex", help="Codex CLI executable path")
            command.add_argument("--model", help="Optional model override for the local CLI")
            command.add_argument("--timeout", type=int, default=300)
            command.add_argument("--prepare-only", action="store_true", help="Only create model task packets, no inference")
    return result


def run(args):
    if args.command == "build":
        library = build(args.sources, args.output)
        print(json.dumps({"output": str(args.output), "experience_count": library["experience_count"],
                          "status_counts": library["status_counts"]}, ensure_ascii=False))
        return 0
    library = read_json(args.kb)
    boundaries = [{"id": r["id"], "statement": r["statement"], "status": r["status"]}
                  for r in library["experiences"] if r["status"] == "needs_review"]
    if args.command == "validate":
        ids = [r["id"] for r in library["experiences"]]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate experience IDs")
        for rule in library["experiences"]:
            validate_schema(rule, "experience.schema.json")
        print(json.dumps({"valid": True, "count": len(ids)}))
        return 0

    paths = discover(args.input)
    if args.command == "review" and not args.prepare_only:
        with isolated_profile() as profile:
            return run_batch(args, library, boundaries, paths, profile)
    return run_batch(args, library, boundaries, paths, None)


def run_batch(args, library, boundaries, paths, profile):
    results = []
    errors = []
    trace_root = args.output.parent / (args.output.stem + "_traces")
    for path in paths:
        start = time.monotonic()
        try:
            chart = load_chart(path, args.organization)
            rules, trace = retrieve(library, chart)
            if args.command == "retrieve":
                results.append({"chart_id": chart["chart_id"], "context": {
                    k: chart[k] for k in ["family", "media", "organization"]}, "retrieval": trace})
                continue
            folder = trace_root / chart["chart_id"]
            folder.mkdir(parents=True, exist_ok=True)
            write_json(folder / "retrieval.json", trace)
            if args.prepare_only:
                write_json(folder / "task.json", {"chart_id": chart["chart_id"],
                           "image": chart["image"], "prompt": make_prompt(chart, rules, boundaries)})
                results.append({"chart_id": chart["chart_id"], "status": "prepared_only", "task": str(folder / "task.json")})
            else:
                answer = review_chart(chart, rules, folder, profile, args.codex, args.model, args.timeout, boundaries)
                write_json(folder / "result.json", answer)
                results.append(answer)
            write_json(folder / "run.json", {"elapsed_seconds": round(time.monotonic() - start, 3),
                       "retrieved_count": len(rules), "model_override": args.model, "image_attached": True})
        except Exception as error:
            errors.append({"chart_id": path.name, "error_type": type(error).__name__, "message": str(error)})
        # An interrupted run still leaves a well-formed partial report.
        write_json(args.output, {"schema_version": 1, "status": "incomplete", "charts": results, "errors": errors})
    payload = {"schema_version": 1, "status": "incomplete" if errors else (
               "prepared_only" if getattr(args, "prepare_only", False) else "complete"),
               "library_id": library["library_id"], "planned_count": len(paths),
               "completed_count": len(results), "charts": results, "errors": errors}
    write_json(args.output, payload)
    print(json.dumps({k: v for k, v in payload.items() if k not in ["charts", "errors"]}, ensure_ascii=False))
    return 2 if errors else 0


def main():
    try:
        return run(parser().parse_args())
    except Exception as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        return 2
