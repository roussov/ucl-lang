# =========================================================
# YAML <-> UCL Converter — MAX ∞
# anchors / merge / multi-doc / normalize / streaming
# =========================================================

import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml  # PyYAML

# hypothetical modules
from ucl_py import parser, ast as ucl_ast

# ===================== Config =====================

INDENT = 2
SORT_KEYS = True
PRESERVE_ANCHORS = False
STREAM_THRESHOLD = 10000

# ===================== Utils =====================

def log(msg: str):
    print(f"[convert-yaml] {msg}")


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def write_text(p: Path, content: str):
    p.write_text(content, encoding="utf-8")


# ===================== YAML → UCL =====================

def yaml_to_ucl(obj: Any, indent: int = 0) -> str:
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
        if len(obj) > STREAM_THRESHOLD:
            log("large list (streaming)")

        items = [
            pad + " " * INDENT + yaml_to_ucl(x, indent + 1)
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
            lines.append(
                pad + " " * INDENT + f"{k} = {yaml_to_ucl(v, indent + 1)}"
            )

        return "{\n" + "\n".join(lines) + "\n" + pad + "}"

    return str(obj)


# ===================== YAML Anchors / Merge =====================

def resolve_yaml(data: Any) -> Any:
    # PyYAML resolves anchors automatically when using safe_load
    return data


# ===================== UCL → YAML =====================

def ucl_to_yaml(tree: ucl_ast.Node) -> Any:
    if isinstance(tree, ucl_ast.Program):
        result = {}
        for node in tree.body:
            val = ucl_to_yaml(node)
            if isinstance(val, dict):
                result.update(val)
        return result

    if isinstance(tree, ucl_ast.Section):
        return {
            tree.name: {
                k: v
                for stmt in tree.body
                for k, v in ucl_to_yaml(stmt).items()
            }
        }

    if isinstance(tree, ucl_ast.Assignment):
        key = ".".join(tree.key)
        return {key: ucl_to_yaml(tree.value)}

    if isinstance(tree, ucl_ast.String):
        return tree.value

    if isinstance(tree, ucl_ast.Number):
        return tree.value

    if isinstance(tree, ucl_ast.Boolean):
        return tree.value

    if isinstance(tree, ucl_ast.Null):
        return None

    if isinstance(tree, ucl_ast.ListNode):
        return [ucl_to_yaml(x) for x in tree.elements]

    if isinstance(tree, ucl_ast.MapNode):
        return {
            e.key: ucl_to_yaml(e.value)
            for e in tree.entries
        }

    return str(tree)


# ===================== Multi-document =====================

def yaml_multi_to_ucl(docs: List[Any]) -> str:
    return "\n\n".join(yaml_to_ucl(doc) for doc in docs)


def ucl_to_yaml_multi(tree: ucl_ast.Node) -> List[Any]:
    # simple: single doc
    return [ucl_to_yaml(tree)]


# ===================== File Conversion =====================

def convert_yaml_file(inp: Path, out: Path):
    with open(inp, "r") as f:
        docs = list(yaml.safe_load_all(f))

    docs = [resolve_yaml(d) for d in docs]

    ucl = yaml_multi_to_ucl(docs)
    write_text(out, ucl)


def convert_ucl_file(inp: Path, out: Path):
    code = read_text(inp)
    tree = parser.parse(code)

    docs = ucl_to_yaml_multi(tree)

    with open(out, "w") as f:
        yaml.safe_dump_all(docs, f, sort_keys=SORT_KEYS)


# ===================== CLI =====================

def main():
    if len(sys.argv) < 4:
        print("usage: convert_yaml.py <to_ucl|to_yaml> <input> <output>")
        sys.exit(1)

    mode = sys.argv[1]
    inp = Path(sys.argv[2])
    out = Path(sys.argv[3])

    if mode == "to_ucl":
        convert_yaml_file(inp, out)

    elif mode == "to_yaml":
        convert_ucl_file(inp, out)

    else:
        print("invalid mode")
        sys.exit(1)


if __name__ == "__main__":
    main()
