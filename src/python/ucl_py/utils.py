# =========================================================
# UCL Utils — MAX ∞
# io / str / collections / perf / retry / logging / hash
# =========================================================

import os
import time
import json
import hashlib
import functools
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional


# ===================== Logging =====================

def log(msg: str, level: str = "INFO"):
    print(f"[{level}] {msg}")


def log_json(data: Dict[str, Any]):
    print(json.dumps(data, indent=2))


# ===================== File I/O =====================

def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(read_file(path))


def write_json(path: Path, data: Dict[str, Any]):
    write_file(path, json.dumps(data, indent=2))


# ===================== Strings =====================

def normalize_ws(s: str) -> str:
    return "\n".join(line.strip() for line in s.splitlines())


def indent(s: str, n: int) -> str:
    pad = " " * n
    return "\n".join(pad + line for line in s.splitlines())


def ensure_newline(s: str) -> str:
    return s if s.endswith("\n") else s + "\n"


# ===================== Collections =====================

def flatten(lst: Iterable[Any]) -> List[Any]:
    out = []
    for x in lst:
        if isinstance(x, list):
            out.extend(flatten(x))
        else:
            out.append(x)
    return out


def uniq(lst: Iterable[Any]) -> List[Any]:
    seen = set()
    out = []
    for x in lst:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def group_by(items: Iterable[Any], key_fn: Callable) -> Dict[Any, List[Any]]:
    out: Dict[Any, List[Any]] = {}
    for item in items:
        k = key_fn(item)
        out.setdefault(k, []).append(item)
    return out


# ===================== Hash =====================

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_file(path: Path) -> str:
    return sha256(path.read_bytes())


# ===================== Timing =====================

def now() -> float:
    return time.perf_counter()


def timeit(fn: Callable):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        start = now()
        result = fn(*args, **kwargs)
        duration = now() - start
        log(f"{fn.__name__} took {duration:.6f}s", "DEBUG")
        return result
    return wrapper


# ===================== Retry =====================

def retry(fn: Callable, retries: int = 3, delay: float = 0.1):
    for i in range(retries):
        try:
            return fn()
        except Exception as e:
            if i == retries - 1:
                raise
            time.sleep(delay)


# ===================== Memoization =====================

def memoize(fn: Callable):
    cache = {}

    @functools.wraps(fn)
    def wrapper(*args):
        if args in cache:
            return cache[args]
        res = fn(*args)
        cache[args] = res
        return res

    return wrapper


# ===================== Safe Ops =====================

def safe_get(d: Dict, key: str, default=None):
    return d[key] if key in d else default


def safe_cast(fn: Callable, value: Any, default=None):
    try:
        return fn(value)
    except Exception:
        return default


# ===================== Env =====================

def getenv(key: str, default=None):
    return os.environ.get(key, default)


# ===================== CLI Helpers =====================

def die(msg: str, code: int = 1):
    log(msg, "ERROR")
    raise SystemExit(code)


def require(cond: bool, msg: str):
    if not cond:
        die(msg)


# ===================== Example =====================

if __name__ == "__main__":
    log("test")
    print(flatten([1, [2, [3]]]))
    print(uniq([1, 2, 2, 3]))
    print(group_by(["a", "ab", "b"], key_fn=lambda x: x[0]))
