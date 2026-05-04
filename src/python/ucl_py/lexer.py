# =========================================================
# UCL Lexer — MAX ∞
# tokens / positions / errors / comments / extensible
# =========================================================

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional


# ===================== Token Types =====================

class TokenType(Enum):
    IDENT = auto()
    NUMBER = auto()
    STRING = auto()
    BOOLEAN = auto()
    NULL = auto()

    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()

    LPAREN = auto()
    RPAREN = auto()

    EQUAL = auto()
    COMMA = auto()
    DOT = auto()

    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()

    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    AND = auto()
    OR = auto()
    NOT = auto()

    IF = auto()
    ELSE = auto()
    INCLUDE = auto()

    EOF = auto()


# ===================== Token =====================

@dataclass
class Token:
    type: TokenType
    value: Optional[str]
    line: int
    column: int


# ===================== Lexer =====================

class Lexer:
    def __init__(self, text: str, file: str = "<input>"):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.file = file

    # ---------- Core ----------

    def peek(self):
        return self.text[self.pos] if self.pos < len(self.text) else None

    def advance(self):
        ch = self.peek()
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    # ---------- Helpers ----------

    def skip_whitespace(self):
        while self.peek() and self.peek().isspace():
            self.advance()

    def skip_comment(self):
        if self.peek() == "#":
            while self.peek() and self.peek() != "\n":
                self.advance()

    # ---------- Tokens ----------

    def read_identifier(self):
        start_col = self.col
        value = ""

        while self.peek() and (self.peek().isalnum() or self.peek() in "_-"):
            value += self.advance()

        keywords = {
            "true": TokenType.BOOLEAN,
            "false": TokenType.BOOLEAN,
            "null": TokenType.NULL,
            "if": TokenType.IF,
            "else": TokenType.ELSE,
            "include": TokenType.INCLUDE,
        }

        ttype = keywords.get(value, TokenType.IDENT)
        return Token(ttype, value, self.line, start_col)

    def read_number(self):
        start_col = self.col
        value = ""

        while self.peek() and (self.peek().isdigit() or self.peek() == "."):
            value += self.advance()

        return Token(TokenType.NUMBER, value, self.line, start_col)

    def read_string(self):
        start_col = self.col
        quote = self.advance()
        value = ""

        while self.peek() and self.peek() != quote:
            if self.peek() == "\\":
                self.advance()
                value += self.advance()
            else:
                value += self.advance()

        self.advance()  # closing quote
        return Token(TokenType.STRING, value, self.line, start_col)

    # ---------- Main ----------

    def next_token(self) -> Token:
        while self.peek():

            self.skip_whitespace()
            self.skip_comment()

            ch = self.peek()
            if not ch:
                break

            # identifiers
            if ch.isalpha() or ch == "_":
                return self.read_identifier()

            # numbers
            if ch.isdigit():
                return self.read_number()

            # strings
            if ch in "\"'":
                return self.read_string()

            # operators / symbols
            if ch == "{":
                self.advance()
                return Token(TokenType.LBRACE, "{", self.line, self.col)
            if ch == "}":
                self.advance()
                return Token(TokenType.RBRACE, "}", self.line, self.col)
            if ch == "[":
                self.advance()
                return Token(TokenType.LBRACKET, "[", self.line, self.col)
            if ch == "]":
                self.advance()
                return Token(TokenType.RBRACKET, "]", self.line, self.col)

            if ch == "(":
                self.advance()
                return Token(TokenType.LPAREN, "(", self.line, self.col)
            if ch == ")":
                self.advance()
                return Token(TokenType.RPAREN, ")", self.line, self.col)

            if ch == "=":
                self.advance()
                if self.peek() == "=":
                    self.advance()
                    return Token(TokenType.EQ, "==", self.line, self.col)
                return Token(TokenType.EQUAL, "=", self.line, self.col)

            if ch == "!":
                self.advance()
                if self.peek() == "=":
                    self.advance()
                    return Token(TokenType.NEQ, "!=", self.line, self.col)
                return Token(TokenType.NOT, "!", self.line, self.col)

            if ch == "+":
                self.advance()
                return Token(TokenType.PLUS, "+", self.line, self.col)
            if ch == "-":
                self.advance()
                return Token(TokenType.MINUS, "-", self.line, self.col)
            if ch == "*":
                self.advance()
                return Token(TokenType.STAR, "*", self.line, self.col)
            if ch == "/":
                self.advance()
                return Token(TokenType.SLASH, "/", self.line, self.col)

            if ch == ",":
                self.advance()
                return Token(TokenType.COMMA, ",", self.line, self.col)

            if ch == ".":
                self.advance()
                return Token(TokenType.DOT, ".", self.line, self.col)

            if ch == "<":
                self.advance()
                return Token(TokenType.LT, "<", self.line, self.col)

            if ch == ">":
                self.advance()
                return Token(TokenType.GT, ">", self.line, self.col)

            if ch == "&":
                self.advance()
                if self.peek() == "&":
                    self.advance()
                    return Token(TokenType.AND, "&&", self.line, self.col)

            if ch == "|":
                self.advance()
                if self.peek() == "|":
                    self.advance()
                    return Token(TokenType.OR, "||", self.line, self.col)

            # unknown
            raise SyntaxError(f"{self.file}:{self.line}:{self.col} unknown char: {ch}")

        return Token(TokenType.EOF, None, self.line, self.col)


# ===================== API =====================

def tokenize(code: str) -> List[Token]:
    lexer = Lexer(code)
    tokens = []

    while True:
        tok = lexer.next_token()
        tokens.append(tok)
        if tok.type == TokenType.EOF:
            break

    return tokens


# ===================== Example =====================

if __name__ == "__main__":
    code = """
    app {
      name = "vitte"
      version = 1
    }
    """

    for t in tokenize(code):
        print(t)
