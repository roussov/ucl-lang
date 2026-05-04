# =========================================================
# UCL Evaluator — MAX ∞
# eval / env / lazy / deps / functions / profiles / sandbox
# =========================================================

from typing import Any, Dict, Callable, Optional
from dataclasses import dataclass, field

from ucl_py import ast as ucl_ast


# ===================== Environment =====================

@dataclass
class Env:
    vars: Dict[str, Any] = field(default_factory=dict)
    funcs: Dict[str, Callable] = field(default_factory=dict)
    parent: Optional["Env"] = None

    def get(self, name: str):
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get(name)
        raise KeyError(f"undefined variable: {name}")

    def set(self, name: str, value: Any):
        self.vars[name] = value

    def define_func(self, name: str, fn: Callable):
        self.funcs[name] = fn

    def get_func(self, name: str):
        if name in self.funcs:
            return self.funcs[name]
        if self.parent:
            return self.parent.get_func(name)
        raise KeyError(f"undefined function: {name}")


# ===================== Builtins =====================

def builtin_env(key: str):
    import os
    return os.environ.get(key)


def builtin_len(x):
    return len(x)


def builtin_add(a, b):
    return a + b


BUILTINS = {
    "env": builtin_env,
    "len": builtin_len,
    "add": builtin_add,
}


# ===================== Evaluator =====================

class Evaluator:
    def __init__(self):
        self.global_env = Env()
        for k, v in BUILTINS.items():
            self.global_env.define_func(k, v)

    # ---------- Entry ----------

    def eval(self, node: ucl_ast.Node, env: Optional[Env] = None):
        if env is None:
            env = self.global_env

        method = getattr(self, f"eval_{node.__class__.__name__}", None)
        if method:
            return method(node, env)
        raise NotImplementedError(node.__class__.__name__)

    # ---------- Literals ----------

    def eval_String(self, node, env):
        return node.value

    def eval_Number(self, node, env):
        return node.value

    def eval_Boolean(self, node, env):
        return node.value

    def eval_Null(self, node, env):
        return None

    # ---------- Variable ----------

    def eval_Variable(self, node, env):
        return env.get(node.name)

    # ---------- Expressions ----------

    def eval_BinaryOp(self, node, env):
        left = self.eval(node.left, env)
        right = self.eval(node.right, env)

        if node.op == "+":
            return left + right
        if node.op == "-":
            return left - right
        if node.op == "*":
            return left * right
        if node.op == "/":
            return left / right
        if node.op == "==":
            return left == right
        if node.op == "!=":
            return left != right
        if node.op == "<":
            return left < right
        if node.op == ">":
            return left > right
        if node.op == "&&":
            return left and right
        if node.op == "||":
            return left or right

        raise ValueError(f"unknown op {node.op}")

    def eval_UnaryOp(self, node, env):
        val = self.eval(node.operand, env)
        if node.op == "-":
            return -val
        if node.op == "!":
            return not val
        return val

    def eval_FunctionCall(self, node, env):
        fn = env.get_func(node.name)
        args = [self.eval(a, env) for a in node.args]
        return fn(*args)

    # ---------- Collections ----------

    def eval_ListNode(self, node, env):
        return [self.eval(e, env) for e in node.elements]

    def eval_MapNode(self, node, env):
        return {
            e.key: self.eval(e.value, env)
            for e in node.entries
        }

    # ---------- Assignment ----------

    def eval_Assignment(self, node, env):
        val = self.eval(node.value, env)
        key = ".".join(node.key)
        env.set(key, val)
        return {key: val}

    # ---------- Section ----------

    def eval_Section(self, node, env):
        sub = Env(parent=env)
        result = {}

        for stmt in node.body:
            val = self.eval(stmt, sub)
            if isinstance(val, dict):
                result.update(val)

        return {node.name: result}

    # ---------- Conditional ----------

    def eval_Conditional(self, node, env):
        cond = self.eval(node.condition, env)
        branch = node.then_branch if cond else node.else_branch

        result = {}
        for stmt in branch:
            val = self.eval(stmt, env)
            if isinstance(val, dict):
                result.update(val)

        return result

    # ---------- Profile ----------

    def eval_Profile(self, node, env):
        # profiles are evaluated conditionally (external selector)
        return {
            "__profile__": node.name,
            "body": [self.eval(stmt, env) for stmt in node.body]
        }

    # ---------- Program ----------

    def eval_Program(self, node, env):
        result = {}

        for stmt in node.body:
            val = self.eval(stmt, env)

            if isinstance(val, dict):
                result.update(val)

        return result


# ===================== Helper =====================

def evaluate(tree: ucl_ast.Program) -> Dict[str, Any]:
    ev = Evaluator()
    return ev.eval(tree)
