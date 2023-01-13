from util import eprint
from parsing import *

class Compiler:
    def __init__(self, ast:AST):
        self.ast = ast
        self.memory_written = 4
        self.data_section = []

        self.extern_signatures: list[str] = []
        self.procedure_code: list[str] = []
        self.exported_procs: list[str] = []
        self.consts: list[str] = []
        #contains a map of ids to type for evaluating the type of expressions
        self.id_types = {}
        self.loops_count = 0

        self.comparison_map = {
            ">": "gt_u",
            "<": "lt_u",
            ">=": "ge_u",
            "<=": "le_u",
            "==": "eq",
            "!=": "nq",
        }
    
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
                        self.exported_procs.append(f'(export "main" (func ${node["name"]}))')
                    code.append(f"(func ${node['name']}")
                    for p in node["params"]:
                        self.id_types[p.name] = p.type_
                        code.append(f"  (param ${p.name} {self.wasm_type(p.type_)})")
                    if node["type_"]:
                        code.append(f"  (result {self.wasm_type(node['type_'])})")
                    self.id_types[node["name"]] = node["type_"]
                    for n in node["body"]:
                        if n["kind"] == NodeKind.DECL or n["kind"] == NodeKind.MEMDECL:
                            code.append(f"  (local ${n['id']} {self.wasm_type(n['type_'])}) ")
                            self.id_types[n["id"]] = n["type_"]

                    for n in node["body"]:
                        code.extend(self.compile_statement(n))
                    code.append(")")
                    self.procedure_code.append("\n".join(code))
                    #removing declared identifiers
                    for n in node["body"]:
                        if n["kind"] == NodeKind.DECL or n["kind"] == NodeKind.MEMDECL:
                            del self.id_types[n["id"]]
                case NodeKind.CONSTDECL:
                    self.consts.append(f"(global ${node['id']} {self.wasm_type(node['type_'])} ({self.wasm_type(node['type_'])}.const {node['value']}))")
                    self.id_types[node["id"]] = f"const{node['type_']}"

    def compile_statement(self, statement: Statement) -> list[str]:
        result = []
        match statement["kind"]:
            case NodeKind.RETURN:
                expr, _ = self.compile_expression(statement["body"])
                result.append('\n   '.join(expr))
                result.append("return ")
            case NodeKind.ASSIGN:
                expr, _ = self.compile_expression(statement["body"])
                result.append('\n   '.join(expr))
                result.append(f"local.set ${statement['id']}")
            case NodeKind.IF:
                lhs, _ = self.compile_expression(statement["lhs"])
                rhs, type_ = self.compile_expression(statement["rhs"])
                result.append(" ".join(lhs))
                result.append(" ".join(rhs))
                result.append(f"{self.wasm_type(type_)}.{self.comparison_map[statement['comparison']]}")
                result.append("(if")
                result.append("(then")
                for s in statement["body"]:
                    result.append(" ".join(self.compile_statement(s)))
                result.append(")")
                if statement["else"]:
                    result.append("(else")
                    for s in statement["else"]:
                        result.append("".join(self.compile_statement(s)))
                    result.append(")")
                result.append(")")
            case NodeKind.WHILE:
                result.append(f"(loop $l_{self.loops_count}")
                cur_loop = self.loops_count
                self.loops_count += 1
                for s in statement["body"]:
                    result.append(" ".join(self.compile_statement(s)))
                lhs, _ = self.compile_expression(statement["lhs"])
                rhs, type_ = self.compile_expression(statement["rhs"])
                result.append(" ".join(lhs))
                result.append(" ".join(rhs))
                result.append(f"{self.wasm_type(type_)}.{self.comparison_map[statement['comparison']]}")
                result.append(f"br_if $l_{cur_loop}")
                result.append(")")
            case NodeKind.EXPR:
                expr, _ = self.compile_expression(statement["body"])
                result.append(" ".join(expr))
            case NodeKind.MEMDECL:
                result.append("global.get $mem_head")
                result.append(f"local.set ${statement['id']}")
                expr, _ = self.compile_expression(statement['size'])
                result.append(" ".join(expr))
                result.append("global.get $mem_head")
                result.append("i32.add")
                result.append("global.set $mem_head")
            case NodeKind.MEMSTORE:
                result.append(f"local.get ${statement['id']}")
                offset, _ = self.compile_expression(statement["offset"])
                result.append(" ".join(offset))
                val, type_ = self.compile_expression(statement["body"])
                result.append(" ".join(val))
                result.append(f"{self.wasm_type(type_)}.store")
        return result
    
    #returns the code and the type of the code
    def compile_expression(self, expr:ExprFull) -> tuple[list[str], str]:
        result = []
        type_ = ""
        for expr_node in expr:
            if isinstance(expr_node, NameTypePair):
                match expr_node.type_:
                    case "int":
                        result.append(f"i32.const {expr_node.name} ")
                    case "bool":
                        val = expr_node.name
                        result.append(f"i32.const {1 if val == 'true' else 0} ")
                    case "float":
                        result.append(f"f32.const {expr_node.name} ")
                    case "string":
                        #store pointer to start of string
                        result.append(f"global.get $mem_head")
                        result.append(f"i32.const {self.memory_written}")
                        result.append("i32.store")
                        #increment runtime memory head by 4 bytes cause we stored i32
                        result.append("global.get $mem_head")
                        result.append("i32.const 4")
                        result.append("i32.add")
                        result.append(f"global.set $mem_head")
                        
                        #store the length of the string
                        result.append(f"global.get $mem_head")
                        result.append(f"i32.const {len(expr_node.name)}")
                        result.append("i32.store")

                        result.append("global.get $mem_head")
                        result.append("i32.const 4")
                        result.append("i32.add")
                        result.append(f"global.set $mem_head")
                        #push start of this structure on the stack
                        result.append("global.get $mem_head")
                        result.append("i32.const 8")
                        result.append("i32.sub")
                        self.data_section.append(f'"{expr_node.name}"')
                        self.memory_written += len(expr_node.name)
                type_ = expr_node.type_
            elif isinstance(expr_node, FunctionCall):
                for arg in expr_node.args:
                    arg_expr, _ = self.compile_expression(arg)
                    result.extend(arg_expr)
                if expr_node.name not in self.id_types:
                    eprint(f"Undeclared Identifier {expr_node.name}")
                result.append(f" call ${expr_node.name} ")
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
                    case "!":
                        result.append(f"{self.wasm_type(type_)}.load")
                    case _:
                        if expr_node not in self.id_types:
                            eprint(f"Undeclared Identifier {expr_node}")
                        if self.id_types[expr_node].startswith("const"):
                            result.append(f"global.get ${expr_node}")
                        else:
                            result.append(f"local.get ${expr_node}")
                    
        return (result, type_)
    def wasm_type(self, type_: str) -> str:
        if type_ == "float": return "f32"
        else: return "i32"

    #turns the current state of the compiler into a string representation of the completed wat file 
    def save_wasm(self) -> str:
        final = ""
        final += "(module\n"
        for sig in self.extern_signatures: final += f"{sig}\n"
        final += "(memory 1)\n"
        final += '(export "memory" (memory 0))\n'
        for sig in self.exported_procs: final += f"{sig}\n"
        final += f"(global $mem_head (mut i32) (i32.const {self.memory_written}))\n"
        for const in self.consts:
            final += f"{const}\n"
        final += f"(data (i32.const 4) {' '.join(self.data_section)})\n"
        for func in self.procedure_code:
            final += func
        final += ")"
        return final
