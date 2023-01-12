from util import eprint
from parsing import *

class Compiler:
    def __init__(self, ast:AST):
        self.ast = ast
        self.memory_written = 0

        self.extern_signatures: list[str] = []
        self.procedure_code: list[str] = []
        self.exported_procs: list[str] = []
        #contains a map of ids to type for evaluating the type of expressions
        self.id_types = {}
    
    def generate_wasm(self):
        for node in self.ast:
            match node["kind"]:
                case NodeKind.EXTERN:
                    sig = []
                    sig.append(f"(import \"env\" \"{node['name']}\" (func ${node['name']} ")
                    for p in node["params"]:
                        sig.append(f"(param ${p.name} {self.wasm_type(p.type_)})")
                    if node["type_"]:
                        sig.append(f"(result {self.wasm_type(node['type_'])})")
                    sig.append("))")
                    self.id_types[node["name"]] = node["type_"]
                    self.extern_signatures.append("".join(sig))
                case NodeKind.PROC:
                    code = []
                    if node["pub"]:
                        self.exported_procs.append(f"(export (func ${node['name']}))")
                    code.append(f"(func ${node['name']}")
                    for p in node["params"]:
                        code.append(f"  (param ${p.name} {self.wasm_type(p.type_)})")
                    if node["type_"]:
                        code.append(f"  (result {self.wasm_type(node['type_'])})")
                    self.id_types[node["name"]] = node["type_"]
                    for n in node["body"]:
                        if n["kind"] == NodeKind.DECL:
                            code.append(f"  (local ${n['id']} {self.wasm_type(n['type_'])}) ")
                            self.id_types[[n["id"]]] = n["type_"]
                    for n in node["body"]:
                        code.extend(self.compile_statement(n))
                    code.append(")")
                    self.procedure_code.append("\n".join(code))
                    print(self.procedure_code[0])

    def compile_statement(self, statement: Statement) -> list[str]:
        result = []
        match statement["kind"]:
            case NodeKind.RETURN:
                expr, _ = self.compile_expression(statement["body"])
                result.append('\n   '.join(expr))
                result.append("return")
        return result
    
    #returns the code and the type of the code
    def compile_expression(self, expr:ExprFull) -> tuple[list[str], str]:
        result = []
        type_ = ""
        for expr_node in expr:
            if isinstance(expr_node, NameTypePair):
                match expr_node.type_:
                    case "int" | "bool":
                        result.append(f"i32.const {expr_node.name} ")
                    case "float":
                        result.append(f"f32.const {expr_node.name} ")
                    case "string":
                        eprint("Strings Not Implemented")
                type_ = expr_node.type_
            elif isinstance(expr_node, FunctionCall):
                for arg in expr_node.args:
                    arg_expr, _ = self.compile_expression(arg)
                    result.extend(arg_expr)
                if expr_node.name not in self.id_types:
                    eprint(f"Undeclared Identifier {expr_node.name}")
                result.append(f"call ${expr_node.name}")
                type_ = self.id_types[expr_node.name]
            else:
                match expr_node:
                    case "+":
                        result.append(f"{self.wasm_type(type_)}.add")
                    case "-":
                        result.append(f"{self.wasm_type(type_)}.sub")
                    case "*":
                        result.append(f"{self.wasm_type(type_)}.mul")
                    case "/":
                        result.append(f"{self.wasm_type(type_)}.div")
                    case _:
                        print("todo id look up")
                    
        return (result, type_)
    def wasm_type(self, type_: str) -> str:
        if type_ == "float": return "f32"
        else: return "i32"