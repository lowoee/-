from pathlib import Path
import hashlib
import json
import os
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_schema(value, filename):
    from jsonschema import Draft202012Validator

    Draft202012Validator(read_json(ROOT / "schemas" / filename)).validate(value)
