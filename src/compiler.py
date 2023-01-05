from lexer import *
from collections import namedtuple
from enum import Enum, auto
import sys

Variable = namedtuple("Variable", "name type")
Constant = namedtuple("Variable", "name type val")
IdentifierInformation = namedtuple("IdentifierInformation", "type is_var is_const is_func")

class VariableType(Enum):
    INT = auto()
    STR = auto()
    BOOL = auto()
    FLOAT = auto()
    CUSTOM = auto()
    CUSTOM_PTR = auto()

class Function:
    def __init__(self, name: str, params: list[Variable], return_type: VariableType, public:bool, extern:bool):
        self.params = params
        self.return_type = return_type
        self.locals: list[Variable] = []
        self.public = public
        self.body: list[str] = []
        self.name = name
        self.extern = extern

    def add_body(self, code:list[str]):
        self.body = code
    def add_local(self, local:Variable):
        self.locals.append(local)

    def generate_code(self):
        pass

class Compiler:
    expression_tokens = [
        TokenKind.LPAREN, TokenKind.RPAREN, TokenKind.LITERAL_INT, TokenKind.LITERAL_STR,
        TokenKind.ASTERISK, TokenKind.SLASH_FORWARD, TokenKind.PLUS, TokenKind.DASH,
        TokenKind.IDENTIFIER, TokenKind.DOT, TokenKind.LITERAL_FLOAT, TokenKind.LITERAL_BOOL
    ]
    def __init__(self, lexer:Lexer, environment: str):
        self.lexer = lexer
        self.environment = environment

        #holds the name and type of each variable declared in a function
        self.functions:list[Function] = []

        #holds each string literal
        self.strings = []
        #keeps track of how much was written to the data section
        self.data_section_written = 8
        
        #keeps track of while loops added so we can generate custom name for each
        self.loops_added = 0
        
        #external function signatures
        self.extern_functions:list[str] = []
        
        #next function is public
        self.next_proc_public = False

        #keeps track of constants declared
        self.constants: list[Constant] = []


    def compile_until(self, until:list[TokenKind], whitelist:list[TokenKind]):
        result: list[str] = []
        while True:
            token = self.lexer.peek_next_token()
            if token.kind in until:
                return result
            if whitelist:
                if token.kind not in whitelist:
                    print(f"Unexpected Token {token}")
                    sys.exit()
            
            token = self.lexer.next()
            match token.kind:
                #literals
                case TokenKind.LITERAL_STR:
                    self.strings.append(token.value)
                    #a pointer to the start of the string
                    result.append(f"i32.const {self.data_section_written}")
                    #length of the string
                    result.append(f"i32.const {len(token.value)}")
                    self.data_section_written += len(token.value)
                case TokenKind.LITERAL_INT: result.append(f"i32.const {token.value}")
                case TokenKind.LITERAL_FLOAT: result.append(f"f32.const {token.value}")
                case TokenKind.LITERAL_BOOL: result.append(f"i32.const {1 if token.value == 'true' else 0}")

                #arithmetic
                case TokenKind.PLUS:
                    expr_type = self.determine_expression_type([result[len(result)-1]])
                    assert expr_type != None, "Compiler Dev Error cannot determine type of expression"
                    result.append(f"{self.var_type_to_str(expr_type)}.add")
                case TokenKind.DASH:
                    expr_type = self.determine_expression_type([result[len(result)-1]])
                    assert expr_type != None, "Compiler Dev Error cannot determine type of expression"
                    result.append(f"{self.var_type_to_str(expr_type)}.sub")
                case TokenKind.ASTERISK:
                    expr_type = self.determine_expression_type([result[len(result)-1]])
                    assert expr_type != None, "Compiler Dev Error cannot determine type of expression"
                    result.append(f"{self.var_type_to_str(expr_type)}.mul")
                case TokenKind.SLASH_FORWARD:
                    expr_type = self.determine_expression_type([result[len(result)-1]])
                    assert expr_type != None, "Compiler Dev Error cannot determine type of expression"
                    result.append(f"{self.var_type_to_str(expr_type)}.div")

                #comparison
                case TokenKind.DOUBLE_EQUAL: 
                    result.extend(self.compile_until([TokenKind.DO], Compiler.expression_tokens))
                    expr_type = self.determine_expression_type([result[len(result)-1]])
                    result.append(f"{self.var_type_to_str(expr_type)}.eq")
                case TokenKind.NOT_EQUAL: 
                    result.extend(self.compile_until([TokenKind.DO], Compiler.expression_tokens))
                    expr_type = self.determine_expression_type([result[len(result)-1]])
                    result.append(f"{self.var_type_to_str(expr_type)}.ne")
                case TokenKind.LESS_THAN: 
                    result.extend(self.compile_until([TokenKind.DO], Compiler.expression_tokens))
                    expr_type = self.determine_expression_type([result[len(result)-1]])
                    result.append(f"{self.var_type_to_str(expr_type)}.lt_u")
                case TokenKind.GREATER_THAN: 
                    result.extend(self.compile_until([TokenKind.DO], Compiler.expression_tokens))
                    expr_type = self.determine_expression_type([result[len(result)-1]])
                    result.append(f"{self.var_type_to_str(expr_type)}.gt_u")
                case TokenKind.LESS_THAN_EQUAL: 
                    result.extend(self.compile_until([TokenKind.DO], Compiler.expression_tokens))
                    expr_type = self.determine_expression_type([result[len(result)-1]])
                    result.append(f"{self.var_type_to_str(expr_type)}.le_u")
                case TokenKind.GREATER_THAN_EQUAL: 
                    result.extend(self.compile_until([TokenKind.DO], Compiler.expression_tokens))
                    expr_type = self.determine_expression_type([result[len(result)-1]])
                    result.append(f"{self.var_type_to_str(expr_type)}.ge_u")
                
                #control flow
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
                
                #function defintions
                case TokenKind.EXTERN:
                    name = self.lexer.next().value
                    signature = []
                    self.functions.append(Function(name, [], None, False, True))
                    params = self.function_parameters()
                    signature.append(f'(import "{self.environment}" "{name}" (func ${name} ')
                    signature.extend([f"(param {self.var_type_to_str(p.type)}) " for p in params])
                    next_tk = self.lexer.next()
                    if next_tk.kind != TokenKind.END:
                        signature.append(f"(result {self.var_type_to_str(self.token_to_type(next_tk))})")
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
                        return_type = self.token_to_type(next_tk)
                        _ = self.lexer.next()
                    self.functions.append(Function(name, params, return_type,self.next_proc_public, False ))
                    if self.next_proc_public:
                        self.next_proc_public = False
                    body = self.compile_until([TokenKind.END], whitelist=None)
                    self.functions[len(self.functions)-1].add_body(body)
                    _ = self.lexer.next()

                #identifiers (...here we go)
                case TokenKind.IDENTIFIER:
                    match self.lexer.peek_next_token().kind:
                        case TokenKind.LPAREN:
                            _ = self.lexer.next()
                            for fn in self.functions:
                                if token.value == fn.name:
                                    break
                            else:
                                print(f"Undeclared Procedure {token.value}")
                                sys.exit()
                            params = self.compile_until([TokenKind.RPAREN], Compiler.expression_tokens.extend([TokenKind.COMMA]))
                            self.lexer.next()
                            result.extend(params)
                            result.append(f"call ${token.value}")
                        case TokenKind.COLON:
                            _ = self.lexer.next()
                            type_ = self.token_to_type(self.lexer.next())
                            if self.lexer.peek_next_token().kind == TokenKind.SINGLE_EQUAL:
                                _ = self.lexer.next()
                                self.functions[len(self.functions)-1].add_local(Variable(token.value, type_))
                                expr = self.compile_until([TokenKind.END, TokenKind.SEMICOLON], Compiler.expression_tokens)
                                result.extend(expr)
                                result.append(f"local.set ${token.value}")
                            elif self.lexer.peek_next_token().kind == TokenKind.COLON:
                                _ = self.lexer.next()
                                self.constants.append(Constant(token.value, type_, self.lexer.next().value))
                            else:
                                self.functions[len(self.functions)-1].add_local(Variable(token.value, type_))
                        case TokenKind.SINGLE_EQUAL:
                            _ = self.lexer.next()
                            expr = self.compile_until([TokenKind.END, TokenKind.SEMICOLON], Compiler.expression_tokens)
                            result.extend(expr)
                            result.append(f"local.set ${token.value}")
                        case TokenKind.DOT:
                            _ = self.lexer.next()
                        case _:
                            info = self.look_up_identifier(token)
                            if info.is_var:
                                result.append(f"local.get ${token.value}")
                            elif info.is_const:
                                result.append(f"global.get ${token.value}")
                            else:
                                print(f"Unexpected Token {token}")
                                sys.exit()




    def look_up_identifier(self, id:str) -> IdentifierInformation:
        #if id not defined in the current function it wont be a variable in this context'
        #current function is the last added key in the dictionary
        if len(self.functions) < 1:
            pass
        else:
            for var in self.functions[len(self.functions)-1].locals:
                if var.name == id:
                    return IdentifierInformation(var.type, True, False, False)
            for var in self.functions[len(self.functions)-1].params:
                if var.name == id:
                    return IdentifierInformation(var.type, True, False, False)   

        #check if procedure
        for fn in self.functions:
            if id == fn.name:
                return IdentifierInformation(None, False, False, True) 

        #check for constant
        for const in self.constants:
            if id == const.name:
                return IdentifierInformation(const.type, False, True, False)
        

    def determine_expression_type(self, code: list[str]) -> Optional[VariableType]:
        #we wanna look at the last thing first
        code.reverse()
        for inst in code:
            if "i32" in inst:
                return VariableType.INT
            elif "f32" in inst:
                return VariableType.FLOAT
            elif "local.get" in inst:
                name = inst.split("$")[1]
                info = self.look_up_identifier(name)
                return info.type
            elif "global.get" in inst:
                name = inst.split("$")[1]
                info = self.look_up_identifier(name)
                return info.type
            elif "call" in inst:
                name = inst.split("$")[1]
                for func in self.functions:
                    if name == func.name:
                        return func.return_type
            else:
                continue
        return None

    def var_type_to_str(self, v: VariableType) -> str:
        match v:
            case VariableType.INT: return "i32"
            case VariableType.CUSTOM_PTR: return "i32"
            case VariableType.BOOL: return "i32"
            case VariableType.FLOAT: return "f32"
            case _:
                print("COmpiler Dev error specified type has no wasm version")

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
                    param_type = self.lexer.next()
                    params.append(Variable(next_tk.value, self.token_to_type(param_type)))
                case TokenKind.COMMA: pass
                case TokenKind.RPAREN: break
                case _:
                    print(f"Unexpected Token In Procedure Defenition {next_tk}")
                    sys.exit()
            next_tk = self.lexer.next()
        return params

    def token_to_type(self, t: Token, custom_is_ptr:bool=True) -> VariableType:
        match t.kind:
            case TokenKind.TYPE_INT: return VariableType.INT
            case TokenKind.TYPE_BOOL: return VariableType.BOOL
            case TokenKind.TYPE_STR: return VariableType.STR
            case TokenKind.TYPE_FLOAT: return VariableType.FLOAT
            case TokenKind.IDENTIFIER if not custom_is_ptr: return VariableType.CUSTOM
            case TokenKind.IDENTIFIER if custom_is_ptr: return VariableType.CUSTOM_PTR
            case _:
                print(f"Unexpected Token {t}")
                sys.exit(1)
    def save(self, program: list[str]):
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
            f.write(")")
            for const in self.constants:
                f.write(f"(global ${const.name} {self.var_type_to_str(const.type)} ({self.var_type_to_str(const.type)}.const {const.val}))\n")
            for fn in self.functions:
                if fn.extern:
                    continue
                f.write(f"(func ${fn.name}\n")
                for p in fn.params:
                    f.write(f"(param ${p.name} {self.var_type_to_str(p.type)})\n")
                if fn.return_type:
                    f.write(f"(result {self.var_type_to_str(fn.return_type)})\n")
                for l in fn.locals:
                    f.write(f"(local ${l.name} {self.var_type_to_str(l.type)})\n")
                for inst in fn.body:
                    f.write(f"{inst}\n")
                f.write(")\n")
            # for substring in program:
            #     f.write(f"  {substring}\n")
            f.write(")\n")








class Compiler2:
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
        self.defined_types: list[str] = []
        self.constants:list[Variable] = []
        #map of keys to offsets
        self.defined_structs:dict[dict[str, int]] = {}
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
                case TokenKind.STRUCT:
                    name = self.lexer.next().value
                    self.defined_types.append(name)
                    self.defined_structs[name] = {}
                    offset = 0
                    while True:
                        tk = self.lexer.next()
                        if tk.kind == TokenKind.IDENTIFIER:
                            self.defined_structs[name][tk.value] = offset
                            offset += 4
                        elif tk.kind == TokenKind.END:
                            break
                        else:
                            pass
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
                        if self.type_from_token_type(var.type) == None:
                            result.append(f"(local ${var.name} i32) ")
                        else:
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
                            var_type = self.lexer.next()
                            if self.type_from_token_type(var_type.kind) == None:
                                var_type = var_type.value
                                if var_type not in self.defined_types:
                                    print(f"Error: Unknown Type {var_type}")
                                    sys.exit(1)
                            else:
                                var_type = var_type.kind
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
                            elif self.lexer.peek_next_token().kind == TokenKind.COLON:
                                _ = self.lexer.next()
                                value = self.compile_until([TokenKind.END, TokenKind.SEMICOLON], [TokenKind.LITERAL_INT])
                                self.constants.append(var)
                                result.append(f"(global ${token.value} {self.type_from_token_type(var_type)} ({value[0]}))")
                                _ = self.lexer.next()
                                continue
                            elif self.lexer.peek_next_token().kind == TokenKind.LCURLY:
                                _ = self.lexer.next()
                                #pointer to struct start
                                result.append(f"i32.const {self.linear_memory_head}")
                                result.append(f"local.set ${token.value}")
                                while True:
                                    field = self.compile_until([TokenKind.COMMA, TokenKind.RCURLY], Compiler.expression_tokens)
                                    result.append(f"i32.const {self.linear_memory_head}")
                                    result.extend(field)
                                    self.linear_memory_head += 4
                                    result.append("i32.store")
                                    if self.lexer.next().kind == TokenKind.COMMA:
                                        continue
                                    else:
                                        break
                                
                            else:
                                pass
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
                        case TokenKind.LCURLY:
                            _ = self.lexer.next()
                            #pointer to struct start
                            result.append(f"i32.const {self.linear_memory_head}")
                            result.append(f"local.set ${token.value}")
                            while True:
                                field = self.compile_until([TokenKind.COMMA, TokenKind.RCURLY], Compiler.expression_tokens)
                                result.append(f"i32.const {self.linear_memory_head}")
                                result.extend(field)
                                self.linear_memory_head += 4
                                result.append("i32.store")
                                if self.lexer.next().kind == TokenKind.COMMA:
                                    continue
                                else:
                                    break
                        case TokenKind.DOT:
                            #find what struct this guy is
                            _ = self.lexer.next()
                            functions = list(self.defined_functions.keys())
                            name = functions[len(functions)-1]
                            for n in self.defined_functions[name]:
                                if token.value == n.name:
                                    next_t = self.lexer.next()
                                    result.append(f"local.get ${token.value}")
                                    result.append(f"i32.const {self.defined_structs[n.type][next_t.value]}")
                                    result.append("i32.add")
                                    result.append(f"i32.load")
                                
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
                            #check for constant
                            for c in self.constants:
                                if c.name == token.value:
                                    result.append(f"global.get ${token.value}")
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
    
    def type_from_token_type(self, type: TokenKind) -> Optional[str]:
        match type:
            case TokenKind.TYPE_INT: return "i32"
            case TokenKind.TYPE_FLOAT: return "f32"
            case _:
                return None

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
            for name in self.extern_functions:
                f.write(f'(export "{name}" (func ${name}))\n')
            #dont know why we need the 8 but we do
            f.write("(data (i32.const 8) ")
            for string in self.strings:
                f.write(f'"{string}" ')
            f.write(")")
            for substring in program:
                f.write(f"  {substring}\n")

            f.write(")")
    
