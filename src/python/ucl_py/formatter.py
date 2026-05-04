# =========================================================
# UCL Formatter — MAX ∞
# AST-based / stable / idempotent / configurable / diff / CI
# =========================================================

from dataclasses import dataclass
from typing import Any, List, Optional
import difflib

from ucl_py import ast as ucl_ast
from ucl_py import parser  # assume exists


# ===================== Config =====================

@dataclass
class FormatConfig:
    indent_size: int = 2
    use_tabs: bool = False
    max_width: int = 100
    sort_keys: bool = True
    trailing_commas: bool = True
    ensure_newline_eof: bool = True
    normalize_strings: bool = True
    normalize_numbers: bool = True


DEFAULT_CONFIG = FormatConfig()


# ===================== Formatter =====================

class Formatter:
    def __init__(self, config: FormatConfig = DEFAULT_CONFIG):
        self.cfg = config

    # ---------- Helpers ----------

    def indent(self, level: int) -> str:
        if self.cfg.use_tabs:
            return "\t" * level
        return " " * (level * self.cfg.indent_size)

    def normalize_str(self, s: str) -> str:
        if not self.cfg.normalize_strings:
            return s
        return '"' + s.replace('"', '\\"') + '"'

    def normalize_num(self, n: Any) -> str:
        if not self.cfg.normalize_numbers:
            return str(n)
        if isinstance(n, float):
            return str(round(n, 6))
        return str(n)

    # ---------- Entry ----------

    def format(self, node: ucl_ast.Node) -> str:
        out = self.visit(node, 0)
        if self.cfg.ensure_newline_eof:
            out += "\n"
        return out

    def visit(self, node: ucl_ast.Node, level: int) -> str:
        method = getattr(self, f"visit_{node.__class__.__name__}", None)
        if method:
            return method(node, level)
        return ""

    # ---------- Literals ----------

    def visit_String(self, node, level):
        return self.normalize_str(node.value)

    def visit_Number(self, node, level):
        return self.normalize_num(node.value)

    def visit_Boolean(self, node, level):
        return "true" if node.value else "false"

    def visit_Null(self, node, level):
        return "null"

    # ---------- Variable ----------

    def visit_Variable(self, node, level):
        return f"${node.name}"

    # ---------- Expressions ----------

    def visit_BinaryOp(self, node, level):
        return f"{self.visit(node.left, level)} {node.op} {self.visit(node.right, level)}"

    def visit_UnaryOp(self, node, level):
        return f"{node.op}{self.visit(node.operand, level)}"

    def visit_FunctionCall(self, node, level):
        args = ", ".join(self.visit(a, level) for a in node.args)
        return f"{node.name}({args})"

    # ---------- Collections ----------

    def visit_ListNode(self, node, level):
        if not node.elements:
            return "[]"

        lines = []
        for e in node.elements:
            lines.append(
                self.indent(level + 1) + self.visit(e, level + 1)
            )

        return "[\n" + ",\n".join(lines) + "\n" + self.indent(level) + "]"

    def visit_MapNode(self, node, level):
        if not node.entries:
            return "{}"

        entries = node.entries
        if self.cfg.sort_keys:
            entries = sorted(entries, key=lambda e: e.key)

        lines = []
        for e in entries:
            line = (
                self.indent(level + 1)
                + f"{e.key} = {self.visit(e.value, level + 1)}"
            )
            if self.cfg.trailing_commas:
                line += ","
            lines.append(line)

        return "{\n" + "\n".join(lines) + "\n" + self.indent(level) + "}"

    # ---------- Assignment ----------

    def visit_Assignment(self, node, level):
        key = ".".join(node.key)
        return self.indent(level) + f"{key} = {self.visit(node.value, level)}"

    # ---------- Section ----------

    def visit_Section(self, node, level):
        lines = [self.indent(level) + f"{node.name} {{"]

        for stmt in node.body:
            lines.append(self.visit(stmt, level + 1))

        lines.append(self.indent(level) + "}")
        return "\n".join(lines)

    # ---------- Conditional ----------

    def visit_Conditional(self, node, level):
        lines = []

        cond = self.visit(node.condition, level)
        lines.append(self.indent(level) + f"if {cond} {{")

        for stmt in node.then_branch:
            lines.append(self.visit(stmt, level + 1))

        lines.append(self.indent(level) + "}")

        if node.else_branch:
            lines.append(self.indent(level) + "else {")
            for stmt in node.else_branch:
                lines.append(self.visit(stmt, level + 1))
            lines.append(self.indent(level) + "}")

        return "\n".join(lines)

    # ---------- Program ----------

    def visit_Program(self, node, level):
        lines = []
        for stmt in node.body:
            lines.append(self.visit(stmt, level))
        return "\n".join(lines)


# ===================== Diff =====================

def diff(old: str, new: str) -> str:
    return "\n".join(difflib.unified_diff(
        old.splitlines(),
        new.splitlines(),
        lineterm=""
    ))


# ===================== API =====================

def format_code(code: str, config: FormatConfig = DEFAULT_CONFIG) -> str:
    tree = parser.parse(code)
    fmt = Formatter(config)
    return fmt.format(tree)


def check_idempotence(code: str) -> bool:
    formatted = format_code(code)
    return format_code(formatted) == formatted


# ===================== CI =====================

def ci_check(code: str):
    formatted = format_code(code)
    if code != formatted:
        print(diff(code, formatted))
        raise SystemExit(1)


# ===================== Example =====================

if __name__ == "__main__":
    sample = """
    app{name="vitte"version=1}
    """

    out = format_code(sample)
    print(out)
