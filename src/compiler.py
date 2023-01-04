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
        self.defined_functions = []
        self.strings = []
    
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
                case TokenKind.PROC:
                    if self.lexer.peek_next_token().kind != TokenKind.IDENTIFIER:
                        print("Error Expected Identifier after procedure defintion")
                        print(f"Unexpected Token {self.lexer.peek_next_token()}")
                        sys.exit()

                    name = self.lexer.next().value
                    self.defined_functions.append(name)

                    if self.lexer.peek_next_token().kind != TokenKind.LPAREN:
                        print(f"Unexpected Token {self.lexer.next()} expected (")
                        sys.exit()
                    
                    _ = self.lexer.next()

                    next_tk = self.lexer.next()
                    params = 0
                    while True:
                        match next_tk.kind:
                            case TokenKind.IDENTIFIER: params += 1
                            case TokenKind.COMMA: pass
                            case TokenKind.RPAREN: break
                            case _:
                                print(f"Unexpected Token In Procedure Defenition {next_tk}")
                                sys.exit()
                        next_tk = self.lexer.next()

                    result.append(f"(func ${name} ")
                    result.extend(["(param i32) " for _ in range(params)])

                    next_tk = self.lexer.next()
                    match next_tk.kind:
                        case TokenKind.TYPE_INT:
                            result.append("(result i32)") 
                            #consume the do
                            _ = self.lexer.next()
                        case TokenKind.DO: pass
                        case _:
                            print(f"Non return type found {next_tk}")
                            sys.exit()
                    
                    body = self.compile_until([TokenKind.END], None)
                    result.extend(body)
                    result.append(")")
                case TokenKind.DROP: result.append("drop") 
                case TokenKind.EOF: return result

    def save(self, program: list[str]):
        with open("output.wat", "w") as f:
            f.write("(module\n")
            for substring in program:
                f.write(f"  {substring}\n")
            for i, name in enumerate(self.defined_functions):
                if name == "main":
                    f.write(f"(start {i})")
                    break
            else:
                print("No main function declared... please declare one.")
            f.write(")")
        
