# =========================================================
# UCL Validator — MAX ∞
# AST validation / semantic rules / schema / diagnostics
# =========================================================

from typing import List, Dict, Any, Optional

from ucl_py import ast as ucl_ast
from ucl_py.schema import Schema
from ucl_py.diagnostics import Diagnostics, Span, Position, Severity


# ===================== Validator =====================

class Validator:
    def __init__(self, schema: Optional[Schema] = None):
        self.schema = schema
        self.diags = Diagnostics()
        self.symbols: Dict[str, Any] = {}

    # ---------- Entry ----------

    def validate(self, tree: ucl_ast.Program) -> Diagnostics:
        self.visit(tree)

        if self.schema:
            self.validate_schema(tree)

        return self.diags

    # ---------- Visitor ----------

    def visit(self, node):
        method = getattr(self, f"visit_{node.__class__.__name__}", None)
        if method:
            method(node)
        else:
            self.generic_visit(node)

    def generic_visit(self, node):
        for v in vars(node).values():
            if isinstance(v, ucl_ast.Node):
                self.visit(v)
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, ucl_ast.Node):
                        self.visit(item)

    # ---------- Helpers ----------

    def error(self, msg: str, node):
        self.diags.error(msg, self.span(node))

    def warning(self, msg: str, node):
        self.diags.warning(msg, self.span(node))

    def span(self, node):
        if hasattr(node, "pos") and node.pos:
            return Span(
                start=Position(node.pos.line, node.pos.column),
                end=Position(node.pos.line, node.pos.column)
            )
        return None

    # ---------- Rules ----------

    def visit_Assignment(self, node: ucl_ast.Assignment):
        key = ".".join(node.key)

        # duplicate check
        if key in self.symbols:
            self.error(f"duplicate key '{key}'", node)
        else:
            self.symbols[key] = True

        if node.value is None:
            self.error("missing value", node)

        self.visit(node.value)

    def visit_Section(self, node: ucl_ast.Section):
        if not node.name:
            self.error("empty section name", node)

        for stmt in node.body:
            self.visit(stmt)

    def visit_FunctionCall(self, node: ucl_ast.FunctionCall):
        if not node.name:
            self.error("missing function name", node)

        for arg in node.args:
            self.visit(arg)

    def visit_Variable(self, node: ucl_ast.Variable):
        if node.name not in self.symbols:
            self.warning(f"undefined variable '{node.name}'", node)

    def visit_Conditional(self, node: ucl_ast.Conditional):
        self.visit(node.condition)

        for stmt in node.then_branch:
            self.visit(stmt)

        for stmt in node.else_branch:
            self.visit(stmt)

    # ---------- Schema Integration ----------

    def validate_schema(self, tree: ucl_ast.Program):
        from ucl_py.evaluator import evaluate

        try:
            data = evaluate(tree)
            self.schema.validate(data)
        except Exception as e:
            self.diags.error(f"schema validation failed: {e}", None)


# ===================== Multi-pass =====================

class MultiPassValidator:
    def __init__(self, passes: List[Validator]):
        self.passes = passes

    def validate(self, tree: ucl_ast.Program) -> Diagnostics:
        final = Diagnostics()

        for p in self.passes:
            diags = p.validate(tree)
            final.items.extend(diags.items)

        return final


# ===================== Rules API =====================

class Rule:
    def apply(self, node: ucl_ast.Node, validator: Validator):
        pass


class RuleEngine:
    def __init__(self):
        self.rules: List[Rule] = []

    def register(self, rule: Rule):
        self.rules.append(rule)

    def run(self, tree: ucl_ast.Program, validator: Validator):
        for r in self.rules:
            r.apply(tree, validator)


# ===================== Example Custom Rule =====================

class NoDebugRule(Rule):
    def apply(self, node, validator):
        if isinstance(node, ucl_ast.Assignment):
            if "debug" in node.key:
                validator.warning("debug usage", node)


# ===================== API =====================

def validate(tree: ucl_ast.Program, schema: Optional[Schema] = None) -> Diagnostics:
    v = Validator(schema)
    return v.validate(tree)


# ===================== Example =====================

if __name__ == "__main__":
    from ucl_py.parser import parse

    code = """
    app {
        name = "vitte"
        debug = true
        debug = false
    }
    """

    tree = parse(code)

    v = Validator()
    diags = v.validate(tree)

    for d in diags.items:
        print(d.message)
