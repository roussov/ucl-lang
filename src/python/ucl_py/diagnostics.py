# =========================================================
# UCL Diagnostics — MAX ∞
# errors / warnings / notes / codes / spans / LSP / CLI
# =========================================================

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from enum import Enum


# ===================== Severity =====================

class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    NOTE = "note"


# ===================== Position =====================

@dataclass
class Position:
    line: int
    column: int
    file: Optional[str] = None


@dataclass
class Span:
    start: Position
    end: Position


# ===================== Diagnostic =====================

@dataclass
class Diagnostic:
    message: str
    severity: Severity
    code: Optional[str] = None
    span: Optional[Span] = None
    notes: List[str] = field(default_factory=list)
    hints: List[str] = field(default_factory=list)
    related: List["Diagnostic"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message": self.message,
            "severity": self.severity.value,
            "code": self.code,
            "span": {
                "start": asdict(self.span.start),
                "end": asdict(self.span.end)
            } if self.span else None,
            "notes": self.notes,
            "hints": self.hints,
            "related": [r.to_dict() for r in self.related]
        }


# ===================== Builder =====================

class Diagnostics:
    def __init__(self):
        self.items: List[Diagnostic] = []

    def add(self, diag: Diagnostic):
        self.items.append(diag)

    def error(self, msg: str, span: Optional[Span] = None, code: str = None):
        self.add(Diagnostic(msg, Severity.ERROR, code=code, span=span))

    def warning(self, msg: str, span: Optional[Span] = None, code: str = None):
        self.add(Diagnostic(msg, Severity.WARNING, code=code, span=span))

    def info(self, msg: str, span: Optional[Span] = None):
        self.add(Diagnostic(msg, Severity.INFO, span=span))

    def note(self, msg: str, span: Optional[Span] = None):
        self.add(Diagnostic(msg, Severity.NOTE, span=span))

    def has_errors(self) -> bool:
        return any(d.severity == Severity.ERROR for d in self.items)

    def to_json(self) -> List[Dict[str, Any]]:
        return [d.to_dict() for d in self.items]


# ===================== Formatting =====================

def format_diag(d: Diagnostic) -> str:
    loc = ""
    if d.span:
        loc = f"{d.span.start.file}:{d.span.start.line}:{d.span.start.column}: "

    msg = f"{loc}{d.severity.value.upper()}: {d.message}"

    if d.code:
        msg += f" [{d.code}]"

    for note in d.notes:
        msg += f"\n  note: {note}"

    for hint in d.hints:
        msg += f"\n  hint: {hint}"

    return msg


def print_diagnostics(diags: Diagnostics):
    for d in diags.items:
        print(format_diag(d))


# ===================== LSP Conversion =====================

def to_lsp(diags: Diagnostics) -> List[Dict[str, Any]]:
    out = []

    severity_map = {
        Severity.ERROR: 1,
        Severity.WARNING: 2,
        Severity.INFO: 3,
        Severity.NOTE: 4
    }

    for d in diags.items:
        if not d.span:
            continue

        out.append({
            "range": {
                "start": {
                    "line": d.span.start.line - 1,
                    "character": d.span.start.column - 1
                },
                "end": {
                    "line": d.span.end.line - 1,
                    "character": d.span.end.column - 1
                }
            },
            "severity": severity_map[d.severity],
            "code": d.code,
            "message": d.message
        })

    return out


# ===================== Advanced =====================

def merge(a: Diagnostics, b: Diagnostics) -> Diagnostics:
    merged = Diagnostics()
    merged.items = a.items + b.items
    return merged


def group_by_file(diags: Diagnostics) -> Dict[str, List[Diagnostic]]:
    result: Dict[str, List[Diagnostic]] = {}

    for d in diags.items:
        if d.span and d.span.start.file:
            result.setdefault(d.span.start.file, []).append(d)

    return result


def summarize(diags: Diagnostics) -> Dict[str, int]:
    counts = {
        "error": 0,
        "warning": 0,
        "info": 0,
        "note": 0
    }

    for d in diags.items:
        counts[d.severity.value] += 1

    return counts


# ===================== Example =====================

if __name__ == "__main__":
    diags = Diagnostics()

    span = Span(
        start=Position(1, 1, "config.ucl"),
        end=Position(1, 5, "config.ucl")
    )

    d = Diagnostic(
        message="invalid value",
        severity=Severity.ERROR,
        code="E001",
        span=span,
        hints=["expected number", "check input"]
    )

    diags.add(d)

    print_diagnostics(diags)
    print(diags.to_json())
