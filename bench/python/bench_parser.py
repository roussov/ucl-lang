#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gc
import json
import math
import os
import statistics
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable


@dataclass
class BenchCase:
    name: str
    source: str


@dataclass
class BenchResult:
    name: str
    bytes: int
    lines: int
    iterations: int
    warmup: int
    total_ms: float
    mean_ms: float
    median_ms: float
    min_ms: float
    max_ms: float
    stdev_ms: float
    parses_per_sec: float
    mb_per_sec: float


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def add_python_path() -> None:
    root = repo_root()
    candidates = [
        root / "src" / "python",
        root / "src",
        root,
    ]

    for path in candidates:
        if path.exists():
            sys.path.insert(0, str(path))


def synthetic_source(size: int) -> str:
    lines: list[str] = [
        "workspace {",
        '  name = "ucl-bench"',
        "  version = 1",
        "  debug = true",
        "  targets = [\"linux\", \"darwin\", \"windows\"]",
        "}",
        "",
    ]

    i = 0
    while sum(len(x) + 1 for x in lines) < size:
        lines.extend(
            [
                f"service service_{i} {{",
                f'  image = "registry.local/app_{i}:latest"',
                f"  replicas = {1 + (i % 8)}",
                f"  enabled = {'true' if i % 2 == 0 else 'false'}",
                "  resources {",
                f"    cpu = {100 + i}",
                f"    memory = {256 + i * 2}",
                "  }",
                "  env {",
                f'    NODE_ID = "node-{i}"',
                f'    REGION = "eu-west-{i % 3}"',
                "  }",
                "}",
                "",
            ]
        )
        i += 1

    text = "\n".join(lines)
    return text[:size]


def load_files(paths: list[str]) -> list[BenchCase]:
    cases: list[BenchCase] = []

    for raw in paths:
        p = Path(raw)

        if p.is_dir():
            for file in sorted(p.rglob("*")):
                if file.is_file() and file.suffix in {".ucl", ".conf", ".txt"}:
                    cases.append(BenchCase(str(file), file.read_text(encoding="utf-8")))
        elif p.is_file():
            cases.append(BenchCase(str(p), p.read_text(encoding="utf-8")))

    return cases


def resolve_parser() -> Callable[[str], object]:
    add_python_path()

    candidates = [
        ("ucl_py.parser", "parse"),
        ("ucl.parser", "parse"),
        ("parser", "parse"),
        ("src.python.ucl_py.parser", "parse"),
    ]

    errors: list[str] = []

    for module_name, fn_name in candidates:
        try:
            module = __import__(module_name, fromlist=[fn_name])
            fn = getattr(module, fn_name)
            return fn
        except Exception as exc:
            errors.append(f"{module_name}.{fn_name}: {exc}")

    def fallback_parse(text: str) -> dict[str, object]:
        return {
            "kind": "FallbackDocument",
            "lines": [line for line in text.splitlines() if line.strip()],
        }

    print("warning: real parser not found, using fallback parser", file=sys.stderr)
    for err in errors:
        print("  " + err, file=sys.stderr)

    return fallback_parse


def bench_case(
    case: BenchCase,
    parse_fn: Callable[[str], object],
    iterations: int,
    warmup: int,
    disable_gc: bool,
) -> BenchResult:
    for _ in range(warmup):
        parse_fn(case.source)

    if disable_gc:
        gc.disable()

    samples: list[float] = []
    start_total = time.perf_counter()

    try:
        for _ in range(iterations):
            t0 = time.perf_counter()
            parse_fn(case.source)
            t1 = time.perf_counter()
            samples.append((t1 - t0) * 1000.0)
    finally:
        if disable_gc:
            gc.enable()

    total_ms = (time.perf_counter() - start_total) * 1000.0
    mean_ms = statistics.mean(samples)
    median_ms = statistics.median(samples)
    min_ms = min(samples)
    max_ms = max(samples)
    stdev_ms = statistics.stdev(samples) if len(samples) > 1 else 0.0

    byte_count = len(case.source.encode("utf-8"))
    mb = byte_count / (1024 * 1024)
    parses_per_sec = 1000.0 / mean_ms if mean_ms > 0 else math.inf
    mb_per_sec = mb / (mean_ms / 1000.0) if mean_ms > 0 else math.inf

    return BenchResult(
        name=case.name,
        bytes=byte_count,
        lines=case.source.count("\n") + 1,
        iterations=iterations,
        warmup=warmup,
        total_ms=total_ms,
        mean_ms=mean_ms,
        median_ms=median_ms,
        min_ms=min_ms,
        max_ms=max_ms,
        stdev_ms=stdev_ms,
        parses_per_sec=parses_per_sec,
        mb_per_sec=mb_per_sec,
    )


def print_table(results: list[BenchResult]) -> None:
    print(
        f"{'case':36} {'bytes':>10} {'iters':>8} "
        f"{'mean ms':>10} {'min ms':>10} {'p/s':>10} {'MB/s':>10}"
    )
    print("-" * 102)

    for r in results:
        print(
            f"{r.name[:36]:36} {r.bytes:10d} {r.iterations:8d} "
            f"{r.mean_ms:10.4f} {r.min_ms:10.4f} "
            f"{r.parses_per_sec:10.2f} {r.mb_per_sec:10.2f}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark UCL parser")
    parser.add_argument("inputs", nargs="*", help="UCL files or directories")
    parser.add_argument("--iterations", "-n", type=int, default=500)
    parser.add_argument("--warmup", "-w", type=int, default=50)
    parser.add_argument("--size", type=int, default=64 * 1024)
    parser.add_argument("--json", dest="json_path", default="")
    parser.add_argument("--no-gc", action="store_true")
    args = parser.parse_args()

    parse_fn = resolve_parser()

    cases = load_files(args.inputs)
    if not cases:
        cases = [BenchCase(f"synthetic_{args.size}_bytes", synthetic_source(args.size))]

    results = [
        bench_case(
            case=case,
            parse_fn=parse_fn,
            iterations=args.iterations,
            warmup=args.warmup,
            disable_gc=args.no_gc,
        )
        for case in cases
    ]

    print_table(results)

    if args.json_path:
        Path(args.json_path).write_text(
            json.dumps([asdict(r) for r in results], indent=2),
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
