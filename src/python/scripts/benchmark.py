# =========================================================
# Benchmark Framework — MAX ∞
# precision / stats / multi-run / export / CI / extensible
# =========================================================

import time
import statistics
import subprocess
import json
import os
import hashlib
from dataclasses import dataclass, asdict
from typing import Callable, List, Dict, Any


# ===================== Config =====================

ITERATIONS = 1_000_000
WARMUP = 10_000
REPEAT = 5

EXPORT_JSON = "bench.json"
EXPORT_CSV = "bench.csv"

# ===================== Models =====================

@dataclass
class Result:
    name: str
    durations: List[float]
    avg: float
    min: float
    max: float
    p50: float
    p90: float
    p99: float
    ops_per_sec: float
    ns_per_op: float


# ===================== Utils =====================

def now():
    return time.perf_counter()


def percentile(values: List[float], p: float) -> float:
    values = sorted(values)
    k = int(len(values) * p)
    return values[min(k, len(values) - 1)]


def ns_per_op(duration: float, ops: int) -> float:
    return (duration / ops) * 1e9


def ops_per_sec(duration: float, ops: int) -> float:
    return ops / duration if duration > 0 else 0


# ===================== Benchmark Core =====================

def run_once(fn: Callable[[], None]) -> float:
    start = now()
    for _ in range(ITERATIONS):
        fn()
    end = now()
    return end - start


def warmup(fn: Callable[[], None]):
    for _ in range(WARMUP):
        fn()


def benchmark(name: str, fn: Callable[[], None]) -> Result:
    print(f"[bench] {name}")

    warmup(fn)

    durations = []
    for _ in range(REPEAT):
        d = run_once(fn)
        durations.append(d)

    avg = statistics.mean(durations)
    mn = min(durations)
    mx = max(durations)

    return Result(
        name=name,
        durations=durations,
        avg=avg,
        min=mn,
        max=mx,
        p50=percentile(durations, 0.50),
        p90=percentile(durations, 0.90),
        p99=percentile(durations, 0.99),
        ops_per_sec=ops_per_sec(avg, ITERATIONS),
        ns_per_op=ns_per_op(avg, ITERATIONS),
    )


# ===================== Targets =====================

def target_python_math():
    x = 123 + 456


def target_string():
    s = "hello" + "world"


def target_subprocess():
    subprocess.run(["echo", "ok"], stdout=subprocess.DEVNULL)


def target_file_io():
    with open("/tmp/test.txt", "w") as f:
        f.write("test")


def target_hash():
    hashlib.sha256(b"test").hexdigest()


# ===================== DotS Integration =====================

def target_dots_parse():
    subprocess.run(["dots", "run", "parse.dotS"], stdout=subprocess.DEVNULL)


def target_dots_eval():
    subprocess.run(["dots", "run", "eval.dotS"], stdout=subprocess.DEVNULL)


# ===================== Runner =====================

def run_all() -> List[Result]:
    results = []

    targets = [
        ("python_math", target_python_math),
        ("string", target_string),
        ("hash", target_hash),
        ("file_io", target_file_io),
        ("subprocess", target_subprocess),
        ("dots_parse", target_dots_parse),
        ("dots_eval", target_dots_eval),
    ]

    for name, fn in targets:
        results.append(benchmark(name, fn))

    return results


# ===================== Export =====================

def export_json(results: List[Result]):
    with open(EXPORT_JSON, "w") as f:
        json.dump([asdict(r) for r in results], f, indent=2)


def export_csv(results: List[Result]):
    with open(EXPORT_CSV, "w") as f:
        f.write("name,avg,min,max,p50,p90,p99,ops_per_sec,ns_per_op\n")
        for r in results:
            f.write(
                f"{r.name},{r.avg},{r.min},{r.max},{r.p50},{r.p90},{r.p99},{r.ops_per_sec},{r.ns_per_op}\n"
            )


# ===================== CI =====================

def ci_check(results: List[Result]):
    for r in results:
        if r.ops_per_sec < 1000:
            print(f"[FAIL] {r.name}")
            exit(1)


# ===================== Report =====================

def print_report(results: List[Result]):
    print("\n=== BENCH REPORT ===")
    for r in results:
        print(f"{r.name}:")
        print(f"  avg: {r.avg}")
        print(f"  min: {r.min}")
        print(f"  max: {r.max}")
        print(f"  p50: {r.p50}")
        print(f"  p90: {r.p90}")
        print(f"  p99: {r.p99}")
        print(f"  ops/sec: {r.ops_per_sec}")
        print(f"  ns/op: {r.ns_per_op}")


# ===================== Entry =====================

def main():
    results = run_all()
    print_report(results)
    export_json(results)
    export_csv(results)
    ci_check(results)


if __name__ == "__main__":
    main()
