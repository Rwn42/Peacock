from util import eprint
from lexer import *

class Compiler:
    comparison_operator_wasm_table = {
        "less_than": "lt_u",
        "greater_than": "gt_u",
        "less_than_equal": "le_u",
        "greater_than_equal": "ge_u",
        "double_equal": "eq",
        "not_equal": "nq",
    }
    def __init__(self):        
        self.extern_signatures = []

        self.declared_identifiers = {}

        self.functions = []
    
    def compile(self, code):
        for key in code:
            obj = code[key]
            match key:
                case "extern": 
                    self.declared_identifiers[obj["name"]] = obj["return_type"]
                    self.add_extern_signature(obj)
                case "proc":
                    self.declared_identifiers[obj["name"]] = obj["return_type"]
                    print(self.compile_func_statements(obj["body"]))

    
    #compiles function body statements
    def compile_func_statements(self, statements) -> list[str]:
        result = []
        for s in statements:
            obj = statements[s]
            match s:
                case "if":
                    lhs, type_ = self.compile_expr(obj["lhs"])
                    rhs, type_2 = self.compile_expr(obj["rhs"])
                    if type_ != type_2:
                        eprint("mismatched types in comparison.")
                    result.extend(lhs)
                    result.extend(rhs)
                    result.append(self.wasm_type(type_) + "." + Compiler.comparison_operator_wasm_table[obj["comparison"]])
                    result.append("(if")
                    result.append("(then")
                    result.extend(self.compile_func_statements(obj["body"]))
                    result.append(")")
                    if obj["else"]:
                        result.extend(obj["else"])
                        result.append(")")
                    result.append(")")
        return result
    #returns the expression code and the type
    def compile_expr(self, expr) -> tuple[list[str], str]:
        result = []
        type_ = ""
        for part in expr:
            val, kind = part
            match kind:
                case TokenKind.LITERAL_INT:
                    type_ = "int"
                    result.append(f"i32.const {val}")
        
        return (result, type_)


    def add_extern_signature(self, extern_obj):
        signature = []
        signature.append(f'(import "env" "{extern_obj["name"]}" (func ${extern_obj["name"]}')
        for p in extern_obj["params"]:
            signature.append(f"(param ${p} {self.wasm_type(extern_obj['params'][p])})")
        if extern_obj["return_type"]:
            signature.append(f"(result {self.wasm_type(extern_obj['return_type'])})")
        signature.append("))")
        self.extern_signatures.append("".join(signature))

    def wasm_type(self, type_:str) -> str:
        if type_ == "float": return "f32"
        return "i32"
