# =========================================================
# UCL Parser — MAX ∞
# Pratt parser / statements / recovery / AST builder
# =========================================================

from typing import List
from ucl_py.lexer import Token, TokenType, tokenize
from ucl_py import ast as ucl_ast


# ===================== Parser =====================

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    # ---------- Helpers ----------

    def peek(self):
        return self.tokens[self.pos]

    def advance(self):
        tok = self.peek()
        self.pos += 1
        return tok

    def match(self, *types):
        if self.peek().type in types:
            return self.advance()
        return None

    def expect(self, ttype):
        tok = self.peek()
        if tok.type != ttype:
            raise SyntaxError(f"expected {ttype} got {tok.type}")
        return self.advance()

    # ---------- Program ----------

    def parse(self):
        body = []
        while self.peek().type != TokenType.EOF:
            stmt = self.parse_stmt()
            if stmt:
                body.append(stmt)
        return ucl_ast.Program(body=body)

    # ---------- Statements ----------

    def parse_stmt(self):
        tok = self.peek()

        if tok.type == TokenType.IF:
            return self.parse_if()

        if tok.type == TokenType.INCLUDE:
            self.advance()
            path = self.expect(TokenType.STRING).value
            return ucl_ast.Include(path=path)

        if tok.type == TokenType.IDENT:
            return self.parse_assignment_or_section()

        return None

    def parse_assignment_or_section(self):
        keys = [self.expect(TokenType.IDENT).value]

        while self.match(TokenType.DOT):
            keys.append(self.expect(TokenType.IDENT).value)

        if self.match(TokenType.LBRACE):
            body = []
            while not self.match(TokenType.RBRACE):
                stmt = self.parse_stmt()
                if stmt:
                    body.append(stmt)
            return ucl_ast.Section(name=".".join(keys), body=body)

        self.expect(TokenType.EQUAL)
        value = self.parse_expr()

        return ucl_ast.Assignment(key=keys, value=value)

    def parse_if(self):
        self.expect(TokenType.IF)
        cond = self.parse_expr()

        self.expect(TokenType.LBRACE)
        then_body = []
        while not self.match(TokenType.RBRACE):
            then_body.append(self.parse_stmt())

        else_body = []
        if self.match(TokenType.ELSE):
            self.expect(TokenType.LBRACE)
            while not self.match(TokenType.RBRACE):
                else_body.append(self.parse_stmt())

        return ucl_ast.Conditional(
            condition=cond,
            then_branch=then_body,
            else_branch=else_body
        )

    # ---------- Expressions (Pratt) ----------

    def parse_expr(self, rbp=0):
        t = self.advance()
        left = self.nud(t)

        while rbp < self.lbp(self.peek()):
            t = self.advance()
            left = self.led(t, left)

        return left

    def nud(self, tok):
        if tok.type == TokenType.NUMBER:
            return ucl_ast.Number(value=float(tok.value) if "." in tok.value else int(tok.value))

        if tok.type == TokenType.STRING:
            return ucl_ast.String(value=tok.value)

        if tok.type == TokenType.BOOLEAN:
            return ucl_ast.Boolean(value=(tok.value == "true"))

        if tok.type == TokenType.NULL:
            return ucl_ast.Null()

        if tok.type == TokenType.IDENT:
            if self.match(TokenType.LPAREN):
                args = []
                if not self.match(TokenType.RPAREN):
                    while True:
                        args.append(self.parse_expr())
                        if self.match(TokenType.RPAREN):
                            break
                        self.expect(TokenType.COMMA)
                return ucl_ast.FunctionCall(name=tok.value, args=args)

            return ucl_ast.Variable(name=tok.value)

        if tok.type == TokenType.LPAREN:
            expr = self.parse_expr()
            self.expect(TokenType.RPAREN)
            return expr

        if tok.type == TokenType.MINUS:
            return ucl_ast.UnaryOp(op="-", operand=self.parse_expr(100))

        if tok.type == TokenType.NOT:
            return ucl_ast.UnaryOp(op="!", operand=self.parse_expr(100))

        raise SyntaxError(f"unexpected token {tok.type}")

    def led(self, tok, left):
        op = tok.type

        if op in (
            TokenType.PLUS, TokenType.MINUS,
            TokenType.STAR, TokenType.SLASH,
            TokenType.EQ, TokenType.NEQ,
            TokenType.LT, TokenType.GT,
            TokenType.AND, TokenType.OR
        ):
            right = self.parse_expr(self.lbp(tok))
            return ucl_ast.BinaryOp(op=tok.value, left=left, right=right)

        raise SyntaxError(f"invalid operator {tok.type}")

    def lbp(self, tok):
        table = {
            TokenType.OR: 10,
            TokenType.AND: 20,
            TokenType.EQ: 30,
            TokenType.NEQ: 30,
            TokenType.LT: 40,
            TokenType.GT: 40,
            TokenType.PLUS: 50,
            TokenType.MINUS: 50,
            TokenType.STAR: 60,
            TokenType.SLASH: 60,
        }
        return table.get(tok.type, 0)


# ===================== API =====================

def parse(code: str) -> ucl_ast.Program:
    tokens = tokenize(code)
    return Parser(tokens).parse()


# ===================== Example =====================

if __name__ == "__main__":
    code = """
    app {
        name = "vitte"
        version = 1 + 2 * 3

        if version > 1 {
            debug = true
        }
    }
    """

    tree = parse(code)
    from pprint import pprint
    pprint(tree)
