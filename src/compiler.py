from lexer import *
from parsing import *
from enum import Enum, auto

class Id_T(Enum):
    LOCAL = auto()
    GLOBAL = auto()
    FUNC = auto()

class Compiler:
    def __init__(self, parser: Parser):
        self.parser = parser
        self.types = {
            "int": "i32",
            "bool": "i32",
            "float": "f32",
        }
        self.current_type = None
        self.declared_ids = {}

        self.current_tokens = []
        self.current_token_idx = 0
    
        self.loops_added = 0
    def next_token(self) -> Token:
        self.current_token_idx += 1
        return self.current_tokens[self.current_token_idx-1]
    
    def peek_next(self) -> Token:
         return self.current_tokens[self.current_token_idx]
    
    def compile_function(self, name:str) -> list[str]:
        result = []
        f = self.parser.functions[name]
        result.append(f"(func ${name}")
        for p in f["params"]:
            type_ = f['params'][p]
            self.declared_ids[p] = (type_, Id_T.LOCAL)
            if type_.startswith("^"): type_ = "int"
            result.append(f"(param ${p} {self.types[type_]})")
        if f["return_type"]:
            self.declared_ids[name] = (f["return_type"], Id_T.FUNC)
            type_ = f["return_type"]
            if type_.startswith("^"): type_ = "int"
            result.append(f"(result {self.types[type_]})")
        
        for l in f["locals"]:
            type_ = f['locals'][l]
            self.declared_ids[l] = (type_, Id_T.LOCAL)
            if type_.startswith("^"): type_ = "int"
            result.append(f"(local ${l} {self.types[type_]})")

        self.current_tokens = f["body"]
        self.current_token_idx = 0
        result.extend(self.compile_until())
        result.append(")")

        #removing from declared identifiers
        for p in f["params"]:
            del self.declared_ids[p]
        for l in f["locals"]:
            del self.declared_ids[l]
        
        return result

    def push_identifier(self, name:str) -> tuple[list[str], str]:
        result = []
        if name not in self.declared_ids:
            print(f"Undeclared Identifier {name}")
            sys.exit()
        type_ = self.declared_ids[name][0]
        match self.declared_ids[name][1]:
            case Id_T.LOCAL: result.append(f"local.get ${name}")
            case Id_T.GLOBAL: result.append(f"global.get ${name}")
            case Id_T.FUNC: result.append(f"call ${name}")

        return result, type_

    def compile_until(self, until: list[TokenKind] = [TokenKind.END] ) -> list[str]:
        result = []
        while True:
            if self.peek_next().kind in until:
                return result
            tk = self.next_token()
            if tk  == None:
                return result
            match tk.kind:
                case TokenKind.LITERAL_INT:
                    result.append(f"i32.const {tk.value}")
                    self.current_type = "int"
                case TokenKind.LITERAL_FLOAT:
                    result.append(f"f32.const {tk.value}")
                    self.current_type = "float"
                case TokenKind.LITERAL_BOOL:
                    result.append(f"i32.const {1 if tk.value == 'true' else 0}")
                    self.current_type = "bool"
                case TokenKind.LITERAL_STRING: 
                    print("strings not implemented")
                    self.current_type = "string"
                case TokenKind.IDENTIFIER:
                    code, type_ = self.push_identifier(tk.value)
                    result.extend(code)
                    self.current_type = type_
                case TokenKind.SINGLE_EQUAL:
                    var = self.next_token()
                    if var.value not in self.declared_ids:
                        print(f"Undeclared Identifier {var}")
                        sys.exit()
                    else:
                        result.append(f"local.set ${var.value}")

                
                case TokenKind.PLUS: result.append(f"{self.types[self.current_type]}.add")
                case TokenKind.DASH: result.append(f"{self.types[self.current_type]}.mul")
                case TokenKind.ASTERISK: result.append(f"{self.types[self.current_type]}.sub")
                case TokenKind.SLASH_FORWARD: result.append(f"{self.types[self.current_type]}.div")

                case TokenKind.DOUBLE_EQUAL: result.append(f"{self.types[self.current_type]}.eq")
                case TokenKind.NOT_EQUAL: result.append(f"{self.types[self.current_type]}.ne")
                case TokenKind.LESS_THAN: result.append(f"{self.types[self.current_type]}.lt_u")
                case TokenKind.GREATER_THAN: result.append(f"{self.types[self.current_type]}.gt_u")
                case TokenKind.LESS_THAN_EQUAL: result.append(f"{self.types[self.current_type]}.le_u")
                case TokenKind.GREATER_THAN_EQUAL: result.append(f"{self.types[self.current_type]}.ge_u")

                case TokenKind.DO:
                    result.append("(if")
                    result.append("(then")
                    result.extend(self.compile_until([TokenKind.END, TokenKind.ELSE]))
                    result.append(")")
                    if self.peek_next().kind == TokenKind.ELSE:
                        result.append("(else")
                        result.extend(self.compile_until())
                        _ = self.next_token()
                        result.append(")")
                    result.append(")")
                case TokenKind.WHILE:
                    loop_id = self.loops_added
                    self.loops_added += 1
                    result.append(f"(loop ${loop_id}")
                    result.extend(self.compile_until())
                    _ = self.next_token()
                    result.append(f"br_if ${loop_id}")
                    result.append(")")
                case TokenKind.RETURN:
                    result.append("return")
    def save(self):
        with open("./output.wat", "w") as fp:
            fp.write("(module\n")
            for f in self.parser.functions:
                fp.write("\n".join(self.compile_function(f)))
            fp.write(")")






                


    

