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
        #this can just contain names
        self.defined_functions = []
        #these must be full function signatures
        self.imported_functions = []
        self.strings = []
        self.data_written = 8
        self.linear_memory = []
        self.linear_memory_head = 0
        self.environment = "wasi_unstable"
    
    def compile_until(self, until: list[TokenKind], whitelist: list[TokenKind]):
        result: list[str] = []
        while True:
            
            token = self.lexer.peek_next_token()
            if token.kind in until:
                return result
            if whitelist:
                if token.kind not in whitelist:
                    print(f"Unexpected Token {token}")
            
            token = self.lexer.next()
            match token.kind:
                case TokenKind.LITERAL_STR:
                    self.strings.append(token.value)
                   
                    #by compiler convention strings are stored at linear memory position 0
                    code = self.linear_store(self.data_written, 0)
                    
                    #without offset it will be automatically calculated
                    code.extend(self.linear_store(len(token.value)-1))
                    result.extend(code)
                    self.data_written += len(token.value)
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

                    params = self.function_parameters()

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
                case TokenKind.EXTERN:
                    name = self.lexer.next().value
                    signature = []
                    self.defined_functions.append(name)
                    params = self.function_parameters()
                    signature.append(f'(import "{self.environment}" "{name}" (func ${name} ')
                    signature.extend(["(param i32) " for _ in range(params)])
                    next_tk = self.lexer.next()
                    match next_tk.kind:
                        case TokenKind.TYPE_INT:
                            signature.append("(result i32)") 
                            #consume the end
                            _ = self.lexer.next()
                        case TokenKind.END: pass
                        case _:
                            print(f"Non return type found {next_tk}")
                            sys.exit()
                    signature.append("))")
                    self.imported_functions.append("".join(signature))
                case TokenKind.IDENTIFIER:
                    match self.lexer.next().kind:
                        #function call
                        case TokenKind.LPAREN:
                            if token.value not in self.defined_functions:
                                print(f"Undeclared function {token}")
                                sys.exit()
                            params = self.compile_until([TokenKind.RPAREN], Compiler.expression_tokens.extend([TokenKind.COMMA]))
                            self.lexer.next()
                            result.extend(params)
                            result.append(f"call ${token.value}")
                case TokenKind.DROP: result.append("drop") 
                case TokenKind.EOF: return result
                case TokenKind.END: pass
                case TokenKind.COMMA: pass
                case _:
                    print(token)
                    sys.exit()

    #stores a constant and linear memory at a given position
    #or calculates the position based on previous written
    def linear_store(self, num:int, offset = None) -> list[str]:
        result = ["(i32.store "]

        #this constant is the offset in linear memory to store
        if not offset:
            result.append(f"(i32.const {self.linear_memory_head})")
        else:
            result.append(f"(i32.const {offset})")

        self.linear_memory_head += 4
        result.append(f"(i32.const {num})")
        result.append(")")
        return result

    #returns number of function parameters once we have type support
    #will return associated type as well 
    def function_parameters(self) -> int:
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
        return params

    def save(self, program: list[str]):
        with open("output.wat", "w") as f:
            f.write("(module\n")
            for imported_function in self.imported_functions:
                f.write(f"{imported_function}\n")
            f.write("(memory 1)\n")
            f.write('(export "memory" (memory 0))\n')
            #dont know why we need the 8 but we do
            f.write("(data (i32.const 8) ")
            for string in self.strings:
                f.write(f'"{string}" ')
            f.write(")")
            for substring in program:
                f.write(f"  {substring}\n")
            for i, name in enumerate(self.defined_functions):
                if name == "main":
                    f.write(f"(start {i})\n")
                    break
            else:
                print("No main function declared... please declare one.")
            f.write(")")
        
