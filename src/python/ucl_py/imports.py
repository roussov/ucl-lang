# =========================================================
# UCL Import System — MAX ∞
# resolver / cache / cycles / namespaces / sandbox / loader
# =========================================================

from pathlib import Path
from typing import Dict, Set, Optional
from dataclasses import dataclass, field

from ucl_py import parser, ast as ucl_ast


# ===================== Config =====================

DEFAULT_SEARCH_PATHS = [
    Path("."),                # local
    Path("./modules"),        # project modules
    Path("/usr/lib/ucl"),     # global
]


# ===================== Import Context =====================

@dataclass
class ImportContext:
    loaded: Dict[str, ucl_ast.Program] = field(default_factory=dict)
    loading: Set[str] = field(default_factory=set)
    search_paths: list = field(default_factory=lambda: DEFAULT_SEARCH_PATHS.copy())


# ===================== Resolver =====================

def resolve_module(name: str, ctx: ImportContext) -> Path:
    for base in ctx.search_paths:
        candidate = base / (name.replace(".", "/") + ".ucl")
        if candidate.exists():
            return candidate

    raise FileNotFoundError(f"module not found: {name}")


# ===================== Loader =====================

def load_module(name: str, ctx: ImportContext) -> ucl_ast.Program:
    if name in ctx.loaded:
        return ctx.loaded[name]

    if name in ctx.loading:
        raise RuntimeError(f"cyclic import detected: {name}")

    ctx.loading.add(name)

    path = resolve_module(name, ctx)
    code = path.read_text(encoding="utf-8")

    tree = parser.parse(code)

    # resolve nested imports
    process_imports(tree, ctx)

    ctx.loading.remove(name)
    ctx.loaded[name] = tree

    return tree


# ===================== Import Processing =====================

def process_imports(node: ucl_ast.Node, ctx: ImportContext):
    if isinstance(node, ucl_ast.Program):
        new_body = []

        for stmt in node.body:
            if isinstance(stmt, ucl_ast.Include):
                mod = load_module(stmt.path, ctx)

                # inline module
                new_body.extend(mod.body)

            else:
                process_imports(stmt, ctx)
                new_body.append(stmt)

        node.body = new_body

    elif hasattr(node, "__dict__"):
        for v in vars(node).values():
            if isinstance(v, ucl_ast.Node):
                process_imports(v, ctx)
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, ucl_ast.Node):
                        process_imports(item, ctx)


# ===================== Namespacing =====================

def namespace_module(tree: ucl_ast.Program, name: str) -> ucl_ast.Program:
    new_body = []

    for stmt in tree.body:
        if isinstance(stmt, ucl_ast.Assignment):
            stmt.key = [name] + stmt.key
        elif isinstance(stmt, ucl_ast.Section):
            stmt.name = f"{name}.{stmt.name}"

        new_body.append(stmt)

    tree.body = new_body
    return tree


# ===================== Cache =====================

class ImportCache:
    def __init__(self):
        self.cache: Dict[str, ucl_ast.Program] = {}

    def get(self, name: str):
        return self.cache.get(name)

    def set(self, name: str, tree: ucl_ast.Program):
        self.cache[name] = tree


# ===================== Sandbox =====================

def is_allowed(path: Path, ctx: ImportContext) -> bool:
    for base in ctx.search_paths:
        try:
            path.relative_to(base)
            return True
        except Exception:
            continue
    return False


# ===================== Safe Loader =====================

def safe_load_module(name: str, ctx: ImportContext) -> ucl_ast.Program:
    path = resolve_module(name, ctx)

    if not is_allowed(path, ctx):
        raise PermissionError(f"forbidden import: {path}")

    return load_module(name, ctx)


# ===================== Entry API =====================

def resolve_all(tree: ucl_ast.Program, ctx: Optional[ImportContext] = None) -> ucl_ast.Program:
    if ctx is None:
        ctx = ImportContext()

    process_imports(tree, ctx)
    return tree


# ===================== Example =====================

if __name__ == "__main__":
    ctx = ImportContext()

    root = load_module("main", ctx)

    print("loaded modules:", list(ctx.loaded.keys()))
