# =========================================================
# TOML <-> UCL Converter — MAX ∞
# tables / arrays-of-tables / normalize / CLI-ready
# =========================================================

import sys
from pathlib import Path
from typing import Any, Dict

import tomllib  # Python 3.11+
import tomli_w  # for writing TOML

# hypothetical UCL modules
from ucl_py import parser, ast as ucl_ast

# ===================== Config =====================

INDENT = 2
SORT_KEYS = True


# ===================== Utils =====================

def log(msg: str):
    print(f"[convert-toml] {msg}")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str):
    path.write_text(content, encoding="utf-8")


# ===================== TOML -> UCL =====================

def toml_to_ucl(data: Dict[str, Any], indent=0) -> str:
    pad = " " * (indent * INDENT)

    lines = []

    for key, value in sorted(data.items()) if SORT_KEYS else data.items():
        if isinstance(value, dict):
            lines.append(pad + key + " {")
            lines.append(toml_to_ucl(value, indent + 1))
            lines.append(pad + "}")
        elif isinstance(value, list):
            if value and isinstance(value[0], dict):
                # array of tables
                for item in value:
                    lines.append(pad + key + " {")
                    lines.append(toml_to_ucl(item, indent + 1))
                    lines.append(pad + "}")
            else:
                items = ", ".join(map(str, value))
                lines.append(pad + f"{key} = [{items}]")
        else:
            if isinstance(value, str):
                value = f"\"{value}\""
            elif value is True:
                value = "true"
            elif value is False:
                value = "false"

            lines.append(pad + f"{key} = {value}")

    return "\n".join(lines)


# ===================== UCL -> TOML =====================

def ucl_to_toml(tree: ucl_ast.Node) -> Dict[str, Any]:
    if isinstance(tree, ucl_ast.Program):
        result = {}
        for node in tree.body:
            result.update(ucl_to_toml(node))
        return result

    if isinstance(tree, ucl_ast.Section):
        return {
            tree.name: {
                k: v
                for stmt in tree.body
                for k, v in ucl_to_toml(stmt).items()
            }
        }

    if isinstance(tree, ucl_ast.Assignment):
        key = ".".join(tree.key)
        return {key: ucl_to_toml(tree.value)}

    if isinstance(tree, ucl_ast.String):
        return tree.value

    if isinstance(tree, ucl_ast.Number):
        return tree.value

    if isinstance(tree, ucl_ast.Boolean):
        return tree.value

    if isinstance(tree, ucl_ast.Null):
        return None

    if isinstance(tree, ucl_ast.ListNode):
        return [ucl_to_toml(x) for x in tree.elements]

    if isinstance(tree, ucl_ast.MapNode):
        return {
            e.key: ucl_to_toml(e.value)
            for e in tree.entries
        }

    return str(tree)


# ===================== File Conversion =====================

def convert_toml_file(inp: Path, out: Path):
    with open(inp, "rb") as f:
        data = tomllib.load(f)

    ucl = toml_to_ucl(data)
    write_text(out, ucl)


def convert_ucl_file(inp: Path, out: Path):
    code = read_text(inp)
    tree = parser.parse(code)
    data = ucl_to_toml(tree)

    with open(out, "wb") as f:
        tomli_w.dump(data, f)


# ===================== CLI =====================

def main():
    if len(sys.argv) < 4:
        print("usage: convert_toml.py <to_ucl|to_toml> <input> <output>")
        sys.exit(1)

    mode = sys.argv[1]
    inp = Path(sys.argv[2])
    out = Path(sys.argv[3])

    if mode == "to_ucl":
        convert_toml_file(inp, out)

    elif mode == "to_toml":
        convert_ucl_file(inp, out)

    else:
        print("invalid mode")
        sys.exit(1)


if __name__ == "__main__":
    main()
