# =========================================================
# JSON <-> UCL Converter — MAX ∞
# normalize / tolerant / schema / streaming / CLI-ready
# =========================================================

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Union, Optional

# hypothetical internal modules
from ucl_py import parser, formatter, ast as ucl_ast


# ===================== Config =====================

INDENT = 2
SORT_KEYS = True
IGNORE_NULL = False
STREAMING_THRESHOLD = 10_000  # number of items


# ===================== Utils =====================

def log(msg: str):
    print(f"[convert] {msg}")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str):
    path.write_text(content, encoding="utf-8")


# ===================== JSON -> UCL =====================

def json_to_ucl(obj: Any, indent: int = 0) -> str:
    pad = " " * (indent * INDENT)

    if obj is None:
        return "null"

    if isinstance(obj, bool):
        return "true" if obj else "false"

    if isinstance(obj, (int, float)):
        return str(obj)

    if isinstance(obj, str):
        return f"\"{obj}\""

    if isinstance(obj, list):
        if not obj:
            return "[]"

        if len(obj) > STREAMING_THRESHOLD:
            log("large list, streaming mode")

        items = [
            pad + " " * INDENT + json_to_ucl(x, indent + 1)
            for x in obj
        ]
        return "[\n" + ",\n".join(items) + "\n" + pad + "]"

    if isinstance(obj, dict):
        if SORT_KEYS:
            items = sorted(obj.items())
        else:
            items = obj.items()

        lines = []
        for k, v in items:
            if v is None and IGNORE_NULL:
                continue
            lines.append(
                pad + " " * INDENT + f"{k} = {json_to_ucl(v, indent + 1)}"
            )

        return "{\n" + "\n".join(lines) + "\n" + pad + "}"

    raise TypeError(f"Unsupported type: {type(obj)}")


# ===================== UCL -> JSON =====================

def ucl_to_json(tree: ucl_ast.Node) -> Any:
    if isinstance(tree, ucl_ast.Program):
        result = {}
        for node in tree.body:
            val = ucl_to_json(node)
            if isinstance(val, dict):
                result.update(val)
        return result

    if isinstance(tree, ucl_ast.Assignment):
        key = ".".join(tree.key)
        return {key: ucl_to_json(tree.value)}

    if isinstance(tree, ucl_ast.Section):
        return {tree.name: {
            k: v for node in tree.body
            for k, v in ucl_to_json(node).items()
        }}

    if isinstance(tree, ucl_ast.String):
        return tree.value

    if isinstance(tree, ucl_ast.Number):
        return tree.value

    if isinstance(tree, ucl_ast.Boolean):
        return tree.value

    if isinstance(tree, ucl_ast.Null):
        return None

    if isinstance(tree, ucl_ast.ListNode):
        return [ucl_to_json(x) for x in tree.elements]

    if isinstance(tree, ucl_ast.MapNode):
        return {
            e.key: ucl_to_json(e.value)
            for e in tree.entries
        }

    if isinstance(tree, ucl_ast.Variable):
        return f"${tree.name}"

    # fallback
    return str(tree)


# ===================== Schema Validation =====================

def validate_schema(data: Dict[str, Any], schema: Optional[Dict[str, Any]]):
    if not schema:
        return

    for key, rules in schema.items():
        if key not in data:
            raise ValueError(f"Missing key: {key}")

        val = data[key]

        if rules["type"] == "number" and not isinstance(val, (int, float)):
            raise TypeError(f"{key} must be number")

        if rules["type"] == "string" and not isinstance(val, str):
            raise TypeError(f"{key} must be string")


# ===================== Streaming =====================

def stream_json_to_ucl(path: Path):
    log("streaming JSON -> UCL")
    with path.open() as f:
        data = json.load(f)
        yield json_to_ucl(data)


# ===================== CLI =====================

def convert_json_file(input_path: Path, output_path: Path):
    data = json.loads(read_text(input_path))
    ucl = json_to_ucl(data)
    write_text(output_path, ucl)


def convert_ucl_file(input_path: Path, output_path: Path):
    code = read_text(input_path)
    tree = parser.parse(code)
    data = ucl_to_json(tree)
    write_text(output_path, json.dumps(data, indent=2))


# ===================== Entry =====================

def main():
    if len(sys.argv) < 4:
        print("usage: convert_json.py <to_ucl|to_json> <input> <output>")
        sys.exit(1)

    mode = sys.argv[1]
    inp = Path(sys.argv[2])
    out = Path(sys.argv[3])

    if mode == "to_ucl":
        convert_json_file(inp, out)

    elif mode == "to_json":
        convert_ucl_file(inp, out)

    else:
        print("invalid mode")
        sys.exit(1)


if __name__ == "__main__":
    main()
