from lexer import *
from collections import namedtuple
from enum import Enum, auto
import sys

class Compiler:
    expression_tokens = [
        TokenKind.LPAREN, TokenKind.RPAREN, TokenKind.LITERAL_INT, TokenKind.LITERAL_STR,
        TokenKind.ASTERISK, TokenKind.SLASH_FORWARD, TokenKind.PLUS, TokenKind.DASH,
        TokenKind.IDENTIFIER,
    ]
    def __init__(self, lexer:Lexer):
        self.lexer = lexer
    
    def compile_until(self, until: list[TokenKind], whitelist: list[TokenKind]):
        result: list[str] = []
        while True:
            token = self.lexer.peek_next_token()
            if token in until:
                return result
            if whitelist:
                if token in whitelist:
                    print(f"Unexpected Token {token}")
            
            token = self.lexer.next()
            match token.kind:
                case TokenKind.LITERAL_INT: result.append(f"i32.const {token.value}")
                case TokenKind.PLUS: result.append("i32.add")
                case TokenKind.DASH: result.append("i32.sub")
                case TokenKind.ASTERISK: result.append("i32.mul")
                case TokenKind.SLASH_FORWARD: result.append("i32.div")
                case TokenKind.DOUBLE_EQUAL: 
                    result.extend(self.compile_until([TokenKind.DO], Compiler.expression_tokens))
                    result.append("i32.eq")
                case TokenKind.NOT_EQUAL: 
                    result.extend(self.compile_until([TokenKind.DO], Compiler.expression_tokens))
                    result.append("i32.ne")
                case TokenKind.LESS_THAN: 
                    result.extend(self.compile_until([TokenKind.DO], Compiler.expression_tokens))
                    result.append("i32.lt_u")
                case TokenKind.GREATER_THAN: 
                    result.extend(self.compile_until([TokenKind.DO], Compiler.expression_tokens))
                    result.append("i32.gt_u")
                case TokenKind.LESS_THAN_EQUAL: 
                    result.extend(self.compile_until([TokenKind.DO], Compiler.expression_tokens))
                    result.append("i32.le_u")
                case TokenKind.GREATER_THAN_EQUAL: 
                    result.extend(self.compile_until([TokenKind.DO], Compiler.expression_tokens))
                    result.append("i32.ge_u")
                case TokenKind.DO:
                    result.append("(if\n(then")
                    result.extend(self.compile_until([TokenKind.END, TokenKind.ELSE], whitelist=None))
                    result.append(")")
                    if self.lexer.next().kind == TokenKind.ELSE:
                        result.append("(else")
                        result.extend(self.compile_until([TokenKind.END], whitelist=None))
                        result.append(")")
                    result.append(")")
                case TokenKind.EOF: return result

    def save(self, program: list[str]):
        with open("output.wat", "w") as f:
            f.write("(module\n")
            for substring in program:
                f.write(f"  {substring}\n")
            f.write(")")
        
