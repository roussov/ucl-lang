# =========================================================
# UCL Tokens — MAX ∞
# enums / categories / metadata / helpers / LSP-ready
# =========================================================

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Dict, Set


# ===================== Token Types =====================

class TokenType(Enum):
    # --- literals ---
    IDENT = auto()
    NUMBER = auto()
    STRING = auto()
    BOOLEAN = auto()
    NULL = auto()

    # --- structure ---
    LBRACE = auto()     # {
    RBRACE = auto()     # }
    LBRACKET = auto()   # [
    RBRACKET = auto()   # ]
    LPAREN = auto()     # (
    RPAREN = auto()     # )

    # --- separators ---
    COMMA = auto()
    DOT = auto()
    COLON = auto()

    # --- operators ---
    EQUAL = auto()      # =
    EQ = auto()         # ==
    NEQ = auto()        # !=
    LT = auto()
    GT = auto()
    LTE = auto()
    GTE = auto()

    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()

    AND = auto()        # &&
    OR = auto()         # ||
    NOT = auto()        # !

    # --- keywords ---
    IF = auto()
    ELSE = auto()
    INCLUDE = auto()
    PROFILE = auto()
    MODULE = auto()

    # --- misc ---
    COMMENT = auto()
    NEWLINE = auto()
    EOF = auto()


# ===================== Token Categories =====================

KEYWORDS: Dict[str, TokenType] = {
    "true": TokenType.BOOLEAN,
    "false": TokenType.BOOLEAN,
    "null": TokenType.NULL,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "include": TokenType.INCLUDE,
    "profile": TokenType.PROFILE,
    "module": TokenType.MODULE,
}

OPERATORS: Set[TokenType] = {
    TokenType.PLUS,
    TokenType.MINUS,
    TokenType.STAR,
    TokenType.SLASH,
    TokenType.EQ,
    TokenType.NEQ,
    TokenType.LT,
    TokenType.GT,
    TokenType.LTE,
    TokenType.GTE,
    TokenType.AND,
    TokenType.OR,
    TokenType.NOT,
}

LITERALS: Set[TokenType] = {
    TokenType.STRING,
    TokenType.NUMBER,
    TokenType.BOOLEAN,
    TokenType.NULL,
}

STRUCTURAL: Set[TokenType] = {
    TokenType.LBRACE,
    TokenType.RBRACE,
    TokenType.LBRACKET,
    TokenType.RBRACKET,
    TokenType.LPAREN,
    TokenType.RPAREN,
}


# ===================== Position =====================

@dataclass
class Position:
    line: int
    column: int
    file: Optional[str] = None


# ===================== Token =====================

@dataclass
class Token:
    type: TokenType
    value: Optional[str]
    start: Position
    end: Position

    # ---------- helpers ----------

    def is_keyword(self) -> bool:
        return self.type in KEYWORDS.values()

    def is_operator(self) -> bool:
        return self.type in OPERATORS

    def is_literal(self) -> bool:
        return self.type in LITERALS

    def is_structural(self) -> bool:
        return self.type in STRUCTURAL

    def to_dict(self):
        return {
            "type": self.type.name,
            "value": self.value,
            "start": vars(self.start),
            "end": vars(self.end),
        }

    def __str__(self):
        return f"{self.type.name}({self.value}) @{self.start.line}:{self.start.column}"


# ===================== Token Factory =====================

def make_token(ttype: TokenType, value: str, line: int, col: int) -> Token:
    start = Position(line, col)
    end = Position(line, col + (len(value) if value else 1))
    return Token(ttype, value, start, end)


# ===================== Reverse Lookup =====================

SYMBOLS: Dict[str, TokenType] = {
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    "[": TokenType.LBRACKET,
    "]": TokenType.RBRACKET,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    ",": TokenType.COMMA,
    ".": TokenType.DOT,
    ":": TokenType.COLON,
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "/": TokenType.SLASH,
    "=": TokenType.EQUAL,
    "<": TokenType.LT,
    ">": TokenType.GT,
}


# ===================== Pretty =====================

def format_token(tok: Token) -> str:
    return f"{tok.type.name:<10} {tok.value or ''} ({tok.start.line}:{tok.start.column})"


# ===================== Debug =====================

def dump_tokens(tokens):
    for t in tokens:
        print(format_token(t))


# ===================== Example =====================

if __name__ == "__main__":
    t = make_token(TokenType.IDENT, "app", 1, 1)
    print(t)
    print(t.to_dict())
