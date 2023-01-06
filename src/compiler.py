from collections import namedtuple
from lexer import *

Variables = dict[str, str]
Variable = namedtuple("Variable", "name type")
Constant = namedtuple("Constant", "name type value")

def comptime_eval(code: list[str]) -> str:
    stack = []
    for inst in code:
        if inst.startswith("i32.const"):
            value = inst.split("i32.const")[1]
            stack.append(int(value))
        elif inst.startswith("f32.const"):
            value = inst.split("f32.const")[1]
            stack.append(float(value))
        elif ".add" in inst:
            a = stack.pop()
            b = stack.pop()
            stack.append(a + b)
        elif ".sub" in inst:
            a = stack.pop()
            b = stack.pop()
            stack.append(a - b)
        elif ".mul" in inst:
            a = stack.pop()
            b = stack.pop()
            stack.append(a * b)
        elif ".div" in inst:
            a = stack.pop()
            b = stack.pop()
            stack.append(a / b)
    return str(stack.pop())



class Function:
    def __init__(self, name: str, params: Variables, return_type: str, public:bool, extern:bool):
        self.params = params
        self.return_type = return_type
    
        self.locals: Variables = {}
        self.public = public
        self.body: list[str] = []
        self.name = name
        self.extern = extern
        self.types: dict[str, str] = {}
    
    def update_types(self, types:dict[str, str]):
        self.types = types

    def add_body(self, code:list[str]):
        self.body = code

    def add_local(self, local:Variable):
        self.locals[local.name] = local.type

    def generate_code(self) -> str:
        result = []
        if self.extern:
            return ""
        result.append(f"(func ${self.name}\n")
        for p in self.params:
            result.append(f"(param ${p} {self.types[self.params[p]]})\n")
        if self.return_type:
            result.append(f"(result {self.types[self.return_type]})\n")
        for l in self.locals:
            result.append(f"(local ${l} {self.types[self.locals[l]]})\n")
        for inst in self.body:
            result.append(f"{inst}\n")
        result.append(")\n")
        return "".join(result)

class Compiler:
    comparison_operators = [
        TokenKind.DOUBLE_EQUAL, TokenKind.NOT_EQUAL,
        TokenKind.LESS_THAN, TokenKind.LESS_THAN_EQUAL,
        TokenKind.GREATER_THAN, TokenKind.GREATER_THAN_EQUAL,
    ]
    def __init__(self, lexer:Lexer, environment: str):
        self.lexer = lexer
        self.environment = environment

        #key is name in peacock language value is the wasm version
        #basically will be i32 or f32
        self.types: dict[str, str] = {"int": "i32", "float": "f32", "bool": "i32", "String": "i32"}

        #declared strings these get sent to the data section
        self.strings: list[str] = []

        #keeps tracks of bytes written to the data section
        self.data_section_written = 8

        #keeps track of functions this is where the meat of the source code is stored
        self.functions: list[Function] = []

        #keeps track of external function signatures
        self.extern_functions: list[str] = []
        
        #keeps track of loops added so each loop has a unique name
        self.loops_added = 0

        #will be true for procedure right after pub keyword
        self.next_proc_public:bool = False

        #map of constant name to tuple of type value
        self.constants: dict[str, tuple[str, str]] = {}

        #map of struct name to struct fields which have name type and offset
        self.structs: dict[str, dict[str, tuple[str, int]]] = {}

        #keeps track of linear memory used
        self.lm_head = 0

    
    #returns code to push the identifer and the type for convience
    def use_declared_identifier(self, identifier_tk: Token) -> tuple[list[str], str]:
        code = []
        type_ = ""
        identifier = identifier_tk.value
        current_function = self.functions[len(self.functions)-1]
        if identifier in current_function.locals:
            type_ = current_function.locals[identifier]
            code.append(f"local.get ${identifier}\n")
            if self.lexer.peek_next_token().kind == TokenKind.AT:
                _ = self.lexer.next()
                field = self.lexer.next().value
                code.append(f"i32.const {self.structs[type_][field][1]}")
                code.append("i32.add")
                code.append(f"{self.types[self.structs[type_][field][0]]}.load")
        elif identifier in current_function.params:
            type_ = current_function.params[identifier]
            code.append(f"local.get ${identifier}\n")
            if self.lexer.peek_next_token().kind == TokenKind.AT:
                _ = self.lexer.next()
                field = self.lexer.next().value
                code.append(f"i32.const {self.structs[type_][field][1]}")
                code.append("i32.add")
                code.append(f"{self.types[self.structs[type_][field][0]]}.load")
        elif self.lexer.peek_next_token().kind == TokenKind.LPAREN:
            for fn in self.functions:
                if fn.name == identifier:
                    #consume lparen
                    _ = self.lexer.next()
                    type_ = fn.return_type
                    #we could compile until a comma and make sure the type matches
                    #but wasm will do it for us so we can ignore it
                    parameter_code, _ = self.compile_expression([TokenKind.RPAREN])
                    #consume rparen
                    _ = self.lexer.next()
                    code.extend(parameter_code)
                    code.append(f"call ${identifier}")
                    break
            else:
                print(f"Undeclared Procedure {identifier_tk}")
                sys.exit()
        elif identifier in self.constants:
            if self.lexer.peek_next_token().kind == TokenKind.LBRACKET:
                _ = self.lexer.next()
                index_expr, _ = self.compile_expression([TokenKind.RBRACKET])
                _ = self.lexer.next()
                code.append(f"global.get ${identifier}")
                code.extend(index_expr)
                code.append("i32.add")
                code.append("i32.const 4")
                code.append("i32.mul")
                code.append("i32.load")
            else:
                code.append(f"global.get ${identifier}")
                type_ = self.constants[identifier][0]
        else:
            print(f"Undeclared Identifier {identifier}")
            sys.exit()
        return (code, type_)


    def add_constant(self, const:Constant):
        self.constants[const.name] = (const.type, const.value)
    #returns the parameter defintion for a function
    def function_parameters(self) -> Variables:
        if self.lexer.peek_next_token().kind != TokenKind.LPAREN:
            print(f"Unexpected Token {self.lexer.next()} expected (")
            sys.exit()

        _ = self.lexer.next()
        next_tk = self.lexer.next()
        params = {}
        while True:
            match next_tk.kind:
                case TokenKind.IDENTIFIER:
                    if self.lexer.next().kind != TokenKind.COLON:
                        print(f"Unexpected Token In Procedure Defenition {next_tk} expected :<type>")
                        sys.exit()
                    param_type = self.lexer.next()
                    params[next_tk.value] = param_type.value
                case TokenKind.COMMA: pass
                case TokenKind.RPAREN: break
                case _:
                    print(f"Unexpected Token In Procedure Defenition {next_tk}")
                    sys.exit()
            next_tk = self.lexer.next()
        return params

    def compile_struct_initialization(self) -> list[str]:
        result = []
        while True:
            code, type_ = self.compile_expression([TokenKind.COMMA, TokenKind.RCURLY])
            result.append(f"i32.const {self.lm_head}")
            result.extend(code)
            result.append(f"{self.types[type_]}.store")
            self.lm_head += 4
            if self.lexer.next().kind == TokenKind.COMMA:
                 continue
            else:
                break

        return result

    #returns the code and the type
    def compile_expression(self, until:list[TokenKind], initial: Token = None) -> tuple[list[str], str]:
        result:list[str] = []
        decided_type: str = None
        while True:
            if self.lexer.peek_next_token().kind in until:   
                break
            if initial:
                token = initial
                initial = None
            else:
                token = self.lexer.next()
            match token.kind:
                #literal values
                case TokenKind.LITERAL_STR:
                    self.strings.append(token.value)
                    #a pointer to the start of the string
                    result.append(f"i32.const {self.data_section_written}")
                    #length of the string
                    result.append(f"i32.const {len(token.value)}")
                    self.data_section_written += len(token.value)
                    decided_type = "String"
                case TokenKind.LITERAL_INT:
                    result.append(f"i32.const {token.value}")
                    decided_type = "int"
                case TokenKind.LITERAL_FLOAT:
                    result.append(f"f32.const {token.value}")
                    decided_type = "float"
                case TokenKind.LITERAL_BOOL:
                    result.append(f"i32.const {1 if token.value == 'true' else 0}")
                    decided_type = "bool"
                
                #arithmetic
                case TokenKind.PLUS:
                    assert decided_type != None, f"Error: Cannot determine type before operation {token}"
                    result.append(f"{self.types[decided_type]}.add")
                case TokenKind.DASH:
                    assert decided_type != None, f"Error: Cannot determine type before operation {token}"
                    result.append(f"{self.types[decided_type]}.sub")
                case TokenKind.ASTERISK:
                    assert decided_type != None, f"Error: Cannot determine type before operation {token}"
                    result.append(f"{self.types[decided_type]}.mul")
                case TokenKind.SLASH_FORWARD:
                    assert decided_type != None, f"Error: Cannot determine type before operation {token}"
                    result.append(f"{self.types[decided_type]}.div")
                
                #identifiers
                case TokenKind.IDENTIFIER:
                    code, type_ = self.use_declared_identifier(token)
                    result.extend(code)
                    decided_type = type_
                case TokenKind.COMMA: pass
                case _:
                    print(f"Error: Unexpected Token {token} in Expression.")
                    sys.exit()

        return (result, decided_type)
    
    def compile_file(self):
        while True:
            token = self.lexer.next()
            if token.kind == TokenKind.EOF:
                return
            
            match token.kind:
                #extern defintions
                case TokenKind.EXTERN:
                    name = self.lexer.next().value
                    signature = []
                    params = self.function_parameters()
                    self.functions.append(Function(name, params, "", False, True))
                    signature.append(f'(import "{self.environment}" "{name}" (func ${name} ')
                    signature.extend([f"(param {self.types[params[p]]}) " for p in params])
                    next_tk = self.lexer.next()
                    if next_tk.kind != TokenKind.END:
                        signature.append(f"(result {self.types[next_tk.value]})")
                        self.functions[len(self.functions)-1].return_type = next_tk.value
                        _ = self.lexer.next()
                    signature.append("))")
                    self.extern_functions.append("".join(signature))
                case TokenKind.PUB:
                    self.next_proc_public = True
                
                case TokenKind.PROC:
                    if self.lexer.peek_next_token().kind != TokenKind.IDENTIFIER:
                        print("Error Expected Identifier after procedure defintion")
                        print(f"Unexpected Token {self.lexer.peek_next_token()}")
                        sys.exit()

                    name = self.lexer.next().value
                    params = self.function_parameters()
                    return_type = None
                    next_tk = self.lexer.next()
                    if next_tk.kind != TokenKind.DO:
                        return_type = next_tk.value
                        _ = self.lexer.next()
                    self.functions.append(Function(name, params, return_type,self.next_proc_public, False ))
                    if self.next_proc_public:
                        self.next_proc_public = False
                    body = self.compile_until([TokenKind.END])
                    _ = self.lexer.next()
                    self.functions[len(self.functions)-1].add_body(body)
                    self.functions[len(self.functions)-1].update_types(self.types)
                case TokenKind.IDENTIFIER:
                    if self.lexer.peek_next_token().kind == TokenKind.COLON:
                        _ = self.lexer.next()
                        type_ = self.lexer.next().value
                        assert self.lexer.next().kind == TokenKind.COLON, "Expected Colon in constant declaration"
                        expression, _ = self.compile_expression([TokenKind.END, TokenKind.SEMICOLON])
                        _ = self.lexer.next()
                        value = comptime_eval(expression)
                        self.add_constant(Constant(token.value, type_, value))
                case TokenKind.STRUCT:
                    name = self.lexer.next().value
                    self.structs[name] = {}
                    offset = 0
                    while self.lexer.peek_next_token().kind != TokenKind.END:
                        field = self.lexer.next().value
                        assert self.lexer.next().kind == TokenKind.COLON, "Expected Colon after field name."
                        type_ = self.lexer.next().value
                        self.structs[name][field] = (type_, offset)
                        offset += 4
                    _ = self.lexer.next()
                    self.types[name] = "i32"
                case TokenKind.MEMORY:
                    mem_name = self.lexer.next().value
                    size = self.lexer.next().value
                    self.add_constant(Constant(mem_name, "int", str(self.lm_head)))
                    self.lm_head += (int(size) * 4)
                    assert self.lexer.next().kind == TokenKind.END, f"Expected End Not {token}"
                case _:
                    print(f"Unexpected Token At Top Level {token}")
                    sys.exit()
                    
                    


                
    def compile_until(self, until: list[TokenKind]) -> list[str]:
        result = []
        while True:
            token = self.lexer.peek_next_token()
            if token.kind in until:
                return result
            token = self.lexer.next()
            match token.kind:
                #comparison
                case TokenKind.DOUBLE_EQUAL: 
                    code, type_ = self.compile_expression([TokenKind.DO])
                    result.extend(code)
                    result.append(f"{self.types[type_]}.eq")
                case TokenKind.NOT_EQUAL: 
                    code, type_ = self.compile_expression([TokenKind.DO])
                    result.extend(code)
                    result.append(f"{self.types[type_]}.ne")
                case TokenKind.LESS_THAN: 
                    code, type_ = self.compile_expression([TokenKind.DO])
                    result.extend(code)
                    result.append(f"{self.types[type_]}.lt_u")
                case TokenKind.GREATER_THAN: 
                    code, type_ = self.compile_expression([TokenKind.DO])
                    result.extend(code)
                    result.append(f"{self.types[type_]}.gt_u")
                case TokenKind.LESS_THAN_EQUAL: 
                    code, type_ = self.compile_expression([TokenKind.DO])
                    result.extend(code)
                    result.append(f"{self.types[type_]}.le_u")
                case TokenKind.GREATER_THAN_EQUAL: 
                    code, type_ = self.compile_expression([TokenKind.DO])
                    result.extend(code)
                    result.append(f"{self.types[type_]}.ge_u")
                
                #control flow
                case TokenKind.IF:
                    code, _ = self.compile_expression(Compiler.comparison_operators)
                    result.extend(code)
                case TokenKind.DO:
                    result.append("(if\n(then")
                    result.extend(self.compile_until([TokenKind.END, TokenKind.ELSE]))
                    result.append(")")
                    if self.lexer.next().kind == TokenKind.ELSE:
                        result.append("(else")
                        result.extend(self.compile_until([TokenKind.END]))
                        _ = self.lexer.next()
                        result.append(")")
                    result.append(")")

                case TokenKind.WHILE:
                    condition = self.compile_until([TokenKind.DO])
                    _ = self.lexer.next()
                    body = self.compile_until([TokenKind.END])
                    _ = self.lexer.next()
                    loop_num = self.loops_added
                    result.append(f"(loop ${loop_num}_loop")
                    result.extend(body)
                    result.extend(condition)
                    result.append(f"br_if ${loop_num}_loop")
                    result.append(")")
                    self.loops_added += 1
                
                #variable declarations
                case TokenKind.IDENTIFIER:
                    match self.lexer.peek_next_token().kind:
                        case TokenKind.COLON:
                            _ = self.lexer.next()
                            function_index = len(self.functions)-1
                            type_ = self.lexer.next().value
                            #add new local variable to function
                            self.functions[function_index].add_local(Variable(token.value, type_))
                            if self.lexer.peek_next_token().kind == TokenKind.SINGLE_EQUAL:
                                _ = self.lexer.next()
                                if self.lexer.peek_next_token().kind == TokenKind.LCURLY:
                                    _ = self.lexer.next()
                                    result.append(f"i32.const {self.lm_head}")
                                    result.append(f"local.set ${token.value}")
                                    result.extend(self.compile_struct_initialization())
                                else:
                                    expression, _ = self.compile_expression([TokenKind.END, TokenKind.SEMICOLON])
                                    _ = self.lexer.next()
                                    result.extend(expression)
                                    result.append(f"local.set ${token.value}")
                        case TokenKind.SINGLE_EQUAL:
                            _ = self.lexer.next()
                            if self.lexer.peek_next_token().kind == TokenKind.LCURLY:
                                _ = self.lexer.next()
                                result.append(f"i32.const {self.lm_head}")
                                result.append(f"local.set ${token.value}")
                                result.extend(self.compile_struct_initialization())
                            else:
                                expression, _ = self.compile_expression([TokenKind.END, TokenKind.SEMICOLON])
                                _ = self.lexer.next()
                                result.extend(expression)
                                result.append(f"local.set ${token.value}")
                        case TokenKind.AT:
                            _ = self.lexer.next()
                            field = self.lexer.next().value
                            assert self.lexer.next().kind == TokenKind.SINGLE_EQUAL, f"Expected = after {token}"
                            expr,_ = self.compile_expression([TokenKind.END, TokenKind.SEMICOLON])
                            _ = self.lexer.next()
                            struct_instance, type_ = self.use_declared_identifier(token)
                            result.extend(struct_instance)
                            result.append(f"i32.const {self.structs[type_][field][1]}")
                            result.append("i32.add")
                            result.extend(expr)
                            result.append(f"{self.types[self.structs[type_][field][0]]}.store")
                        case TokenKind.LBRACKET:
                            _ = self.lexer.next()
                            index_expr, _ = self.compile_expression([TokenKind.RBRACKET])
                            _ = self.lexer.next()
                            assert self.lexer.next().kind == TokenKind.SINGLE_EQUAL, f"Expected Equal Sign {token}"
                            expr, type_ = self.compile_expression([TokenKind.END, TokenKind.SEMICOLON])
                            _ = self.lexer.next()
                            ide, _ = self.use_declared_identifier(token)
                            result.extend(ide)
                            result.extend(index_expr)
                            result.append("i32.add")
                            result.append("i32.const 4")
                            result.append("i32.mul")
                            result.extend(expr)
                            result.append(f"{self.types[type_]}.store")
                        case TokenKind.LPAREN | _:
                            code, type_ = self.use_declared_identifier(token)
                            result.extend(code)
                case TokenKind.RETURN:
                    code, _ = self.compile_expression([TokenKind.END, TokenKind.SEMICOLON])
                    result.extend(code)
                case _:
                    print(f"unexpected token {token}")
                    sys.exit()
    def save(self):
        with open("output.wat", "w") as f:
            f.write("(module\n")
            for imported_function in self.extern_functions:
                f.write(f"{imported_function}\n")
            f.write("(memory 1)\n")
            f.write('(export "memory" (memory 0))\n')
            for function in self.functions:
                    if function.public == True:
                        f.write(f'(export "{function.name}" (func ${function.name}))\n')
            f.write("(data (i32.const 8) ")
            for string in self.strings:
                f.write(f'"{string}" ')
            f.write(")\n")

            for c_name in self.constants:
                c = self.constants[c_name]
                f.write(f"(global ${c_name} {self.types[c[0]]} ({self.types[c[0]]}.const {c[1]}))\n")
            
            for func in self.functions:
                f.write(f"{func.generate_code()}")
            f.write(")")
                      
        


