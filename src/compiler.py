from lexer import *
from collections import namedtuple
from enum import Enum, auto
import sys

Variable = namedtuple("Variable", "name type")

class Compiler:
    expression_tokens = [
        TokenKind.LPAREN, TokenKind.RPAREN, TokenKind.LITERAL_INT, TokenKind.LITERAL_STR,
        TokenKind.ASTERISK, TokenKind.SLASH_FORWARD, TokenKind.PLUS, TokenKind.DASH,
        TokenKind.IDENTIFIER,
    ]
    def __init__(self, lexer:Lexer, environment:str):
        self.lexer = lexer
        #this can just contain names
        self.defined_functions:dict[str, list[Variable]] = {}
        #these must be full function signatures
        self.imported_functions = []
        self.public_functions = []
        self.strings = []
        self.data_written = 8
        self.linear_memory = []
        self.loops_added = 0
        self.linear_memory_head = 0
        self.environment = environment
    
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
                    result.append(f"i32.const {self.data_written}")
                    result.append(f"i32.const {len(token.value)}")
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
                        _ = self.lexer.next()
                        result.append(")")
                    result.append(")")
                case TokenKind.WHILE:
                    condition = self.compile_until([TokenKind.DO], None)
                    _ = self.lexer.next()
                    body = self.compile_until([TokenKind.END], None)
                    _ = self.lexer.next()
                    loop_num = self.loops_added
                    result.append(f"(loop ${loop_num}_loop")
                    result.extend(body)
                    result.extend(condition)
                    result.append(f"br_if ${loop_num}_loop")
                    result.append(")")
                    self.loops_added += 1
                case TokenKind.PUB:
                    row = self.lexer.row
                    col = self.lexer.col
                    pos = self.lexer.pos
                    #print(self.lexer.peek_next_token())
                    if self.lexer.next().kind != TokenKind.PROC:
                        print("ERROR: Expected Proc keyword after public declaration")
                        sys.exit()
                    name = self.lexer.peek_next_token().value
                    self.public_functions.append(name)
                    self.lexer.back(pos, row, col)
                case TokenKind.PROC:
                    if self.lexer.peek_next_token().kind != TokenKind.IDENTIFIER:
                        print("Error Expected Identifier after procedure defintion")
                        print(f"Unexpected Token {self.lexer.peek_next_token()}")
                        sys.exit()

                    name = self.lexer.next().value
                    self.defined_functions[name] = []

                    params = self.function_parameters()
                    #some sort of shallow copy behaviour means i need
                    #a copy of this array at this point
                    params2 = [p for p in params]


                    result.append(f"(func ${name} ")
                    result.extend([f"(param ${p.name} {self.type_from_token_type(p.type)}) " for p in params])
                    self.defined_functions[name] = params
                    
                    next_tk = self.lexer.next()
                    match next_tk.kind:
                        case TokenKind.TYPE_INT:
                            result.append("(result i32)") 
                            #consume the do
                            _ = self.lexer.next()
                        case TokenKind.TYPE_FLOAT:
                            result.append("(result f32)") 
                            #consume the do
                            _ = self.lexer.next()
                        case TokenKind.DO: pass
                        case _:
                            print(f"Non return type found {next_tk}")
                            sys.exit()
            
                    body = self.compile_until([TokenKind.END], None)
                    #consume the end
                    _ = self.lexer.next()
                    for var in self.defined_functions[name]:
                        if var in params2:
                            continue
                        result.append(f"(local ${var.name} {self.type_from_token_type(var.type)}) ")
                    result.extend(body)
                    result.append(")")
                case TokenKind.EXTERN:
                    name = self.lexer.next().value
                    signature = []
                    self.defined_functions[name] = []
                    params = self.function_parameters()
                    signature.append(f'(import "{self.environment}" "{name}" (func ${name} ')
                    signature.extend([f"(param {self.type_from_token_type(p.type)}) " for p in params])
                    next_tk = self.lexer.next()
                    match next_tk.kind:
                        case TokenKind.TYPE_INT:
                            signature.append("(result i32)") 
                            #consume the end
                            _ = self.lexer.next()
                        case TokenKind.TYPE_FLOAT:
                            result.append("(result f32)") 
                            #consume the do
                            _ = self.lexer.next()
                        case TokenKind.END: pass
                        case _:
                            print(f"Non return type found {next_tk}")
                            sys.exit()
                    signature.append("))")
                    self.imported_functions.append("".join(signature))
                case TokenKind.IDENTIFIER:
                    match self.lexer.peek_next_token().kind:
                        #function call
                        case TokenKind.LPAREN:
                            _ = self.lexer.next()
                            if token.value not in self.defined_functions.keys():
                                print(f"Undeclared function {token}")
                                sys.exit()
                            params = self.compile_until([TokenKind.RPAREN], Compiler.expression_tokens.extend([TokenKind.COMMA]))
                            self.lexer.next()
                            result.extend(params)
                            result.append(f"call ${token.value}")

                        #variable declaration
                        case TokenKind.COLON:
                            #consume the colon
                            _ = self.lexer.next()
                            var_type = self.lexer.next().kind
                            var = Variable(token.value, var_type)
                            if self.lexer.peek_next_token().kind == TokenKind.SINGLE_EQUAL:
                                
                                _ = self.lexer.next()
                                assignment_expression = self.compile_until([TokenKind.END, TokenKind.SEMICOLON], Compiler.expression_tokens)
                                #consume the end
                                _ = self.lexer.next()
                                result.extend(assignment_expression)
                                if token.value == "_":
                                    result.append("drop")
                                else:
                                    result.append(f"local.set ${token.value}")
                            #add the variable declaration to the current function
                            functions = list(self.defined_functions.keys())
                            name = functions[len(functions)-1]
                            self.defined_functions[name].append(var)
                        #variable assingment
                        case TokenKind.SINGLE_EQUAL:
                            _ = self.lexer.next()
                            assignment_expression = self.compile_until([TokenKind.END, TokenKind.SEMICOLON], Compiler.expression_tokens)
                            _ = self.lexer.next()
                            result.extend(assignment_expression)
                            result.append(f"local.set ${token.value}")
                        #variable/constant usage not defintion or function call
                        case _:
                            #find what function we in
                            functions = list(self.defined_functions.keys())
                            name = functions[len(functions)-1]

                            #check for local variable
                            for n in self.defined_functions[name]:
                                if n.name == token.value:
                                    result.append(f"local.get ${token.value}")
                                    break
                case TokenKind.DROP: result.append("drop") 
                case TokenKind.EOF: return result
                case TokenKind.END: pass
                case TokenKind.IF: pass
                case TokenKind.COMMA: pass
                case _:
                    print(token)
                    sys.exit()

    #stores a constant and linear memory at a given position
    #or calculates the position based on previous written
    def linear_store(self, num:int, offset = None) -> list[str]:
        result = ["(i32.store "]

        #this constant is the offset in linear memory to store
        if offset is None:
            result.append(f"(i32.const {self.linear_memory_head})")
        else:
            result.append(f"(i32.const {offset})")

        self.linear_memory_head += 4
        result.append(f"(i32.const {num})")
        result.append(")")
        return result

    #returns number of function parameters once we have type support
    #will return associated type as well 
    def function_parameters(self) -> list[Variable]:
        if self.lexer.peek_next_token().kind != TokenKind.LPAREN:
            print(f"Unexpected Token {self.lexer.next()} expected (")
            sys.exit()
                    
        _ = self.lexer.next()

        next_tk = self.lexer.next()
        params = []
        while True:
            match next_tk.kind:
                case TokenKind.IDENTIFIER:
                    if self.lexer.next().kind != TokenKind.COLON:
                        print(f"Unexpected Token In Procedure Defenition {next_tk} expected :<type>")
                        sys.exit()
                    param_type = self.lexer.next().kind
                    params.append(Variable(next_tk.value, param_type))
                case TokenKind.COMMA: pass
                case TokenKind.RPAREN: break
                case _:
                    print(f"Unexpected Token In Procedure Defenition {next_tk}")
                    sys.exit()
            next_tk = self.lexer.next()
        return params
    
    def type_from_token_type(self, type: TokenKind) -> str:
        match type:
            case TokenKind.TYPE_INT: return "i32"
            case TokenKind.TYPE_FLOAT: return "f32"
            case _:
                print(f"Error: unknown type {type}")
                sys.exit()

    #saves the program to a .wat file
    def save(self, program: list[str]):
        with open("output.wat", "w") as f:
            f.write("(module\n")
            for imported_function in self.imported_functions:
                f.write(f"{imported_function}\n")
            f.write("(memory 1)\n")
            f.write('(export "memory" (memory 0))\n')
            # for i, name in enumerate(self.defined_functions.keys()):
            #     if name == "main":
            #         f.write(f'(export "main" (func $main))\n')
            #         break
            # else:
            #     print("No main function declared... please declare one.")
            for name in self.public_functions:
                f.write(f'(export "{name}" (func ${name}))\n')
            #dont know why we need the 8 but we do
            f.write("(data (i32.const 8) ")
            for string in self.strings:
                f.write(f'"{string}" ')
            f.write(")")
            for substring in program:
                f.write(f"  {substring}\n")

            f.write(")")
    
