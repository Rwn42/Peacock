from typing import TypedDict, NamedTuple, Union, Optional
from enum import Enum, auto
from lexer import *
from util import eprint

class NodeKind(Enum):
    EXTERN = auto(),
    PROC = auto(),
    IF = auto(),
    WHILE = auto(),
    DECL = auto(),
    ASSIGN = auto(),
    RETURN = auto(),
    EXPR = auto(),

NameTypePair = NamedTuple("NameTypePair", name=str, type_=str)
FunctionCall = NamedTuple("FunctionCall", name=str, args=list["ExprFull"])

#a value literal would contain a type so strings can be decerned from identifiers.
ExprNode = Union[NameTypePair, str, FunctionCall]
ExprFull = list[ExprNode]
Statement = Union["NodeIf", "NodeReturn", "NodeWhile", "NodeDecl", "NodeAssignment", "NodeExpr"]

FuncParams =  list[NameTypePair]

NodeExtern = TypedDict('NodeExtern', {'name': str, 'params': FuncParams, 'type_': str, "kind":NodeKind})
NodeFunc = TypedDict('NodeFunc', {'name': str, 'params': FuncParams, 'type_': str, "body": list[Statement], "pub": bool, "kind":NodeKind})
NodeIf = TypedDict("NodeIf", {"lhs": ExprFull, "rhs": ExprFull, "comparison": str, "body": list[Statement], "kind":NodeKind, "else":list[Statement]})
NodeWhile = TypedDict("NodeWhile", {"lhs": ExprFull, "rhs": ExprFull, "comparison": str, "body": list[Statement], "kind":NodeKind})
NodeDecl = TypedDict("NodeDecl", {"id": str, "type_": str, "kind":NodeKind})
NodeAssignment = TypedDict("NodeAssignment", {"id": str, "body": ExprFull, "kind":NodeKind})
NodeReturn = TypedDict("NodeReturn", {"body": ExprFull, "kind":NodeKind})
NodeExpr = TypedDict("NodeExpr", {"body": ExprFull, "kind":NodeKind})
AST = list[Union[Statement, "NodeExtern", "NodeFunc"]]


class Parser:
    comparison_tokens = [
        TokenKind.GREATER_THAN, TokenKind.LESS_THAN, TokenKind.DOUBLE_EQUAL, TokenKind.NOT_EQUAL,
        TokenKind.GREATER_THAN_EQUAL, TokenKind.LESS_THAN_EQUAL,
    ]
    expression_tokens = [
        TokenKind.IDENTIFIER, TokenKind.LITERAL_INT, TokenKind.LITERAL_BOOL, TokenKind.LITERAL_FLOAT,
        TokenKind.LITERAL_STRING, TokenKind.PLUS, TokenKind.DASH, TokenKind.ASTERISK, TokenKind.SLASH_FORWARD,
        TokenKind.LPAREN, TokenKind.RPAREN, 
    ]
    type_tokens = [
        TokenKind.IDENTIFIER, TokenKind.HAT
    ]
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.next_proc_pub = False

    #parses top level code and returns the ast representing the program
    def parse(self) -> AST:
        ast: AST = []
        while True:
            token = self.lexer.next()
            match token.kind:
                case TokenKind.EXTERN:
                    name = self.expect(TokenKind.IDENTIFIER, False).value
                    params = self.parse_proc_params()
                    return_type = None
                    if self.lexer.peek_next_token().kind in Parser.type_tokens:
                        return_type = self.parse_type()
                    node:NodeExtern = {"name": name, "params": params, "type_": return_type, "kind":NodeKind.EXTERN}
                    ast.append(node)
                case TokenKind.PROC:
                    name = self.expect(TokenKind.IDENTIFIER, False).value
                    params = self.parse_proc_params()
                    return_type = None
                    if self.lexer.peek_next_token().kind != TokenKind.DO:
                        return_type = self.parse_type()
                    self.expect(TokenKind.DO)
                    body = self.parse_statements_until()
                    self.expect(TokenKind.END)
                    node:NodeFunc = {"name": name, "params": params, "type_": return_type, "pub": self.next_proc_pub, "body":body, "kind":NodeKind.PROC}
                    if self.next_proc_pub:
                        self.next_proc_pub = False
                    ast.append(node)
                case TokenKind.PUB:
                    self.next_proc_pub = True
                    if self.lexer.peek_next_token().kind != TokenKind.PROC:
                        #this expect will always fail if reached
                        self.expect(TokenKind.PROC)
                case TokenKind.NEWLINE: pass
                case TokenKind.EOF: return ast
                case _:
                    eprint(f"Token {token} Not Allowed In Top Level")
    
    #returns statements until a desired token
    def parse_statements_until(self, until: list[TokenKind]=[TokenKind.END]) -> list[Statement]:
        result: list[Statement] = []
        while self.lexer.peek_next_token().kind not in until:
            token = self.lexer.next()
            match token.kind:
                case TokenKind.IF | TokenKind.WHILE:
                    lhs = self.parse_expr_until(Parser.comparison_tokens)
                    comparison = self.lexer.next().value
                    rhs = self.parse_expr_until([TokenKind.DO])
                    _ = self.lexer.next()
                    body = self.parse_statements_until([TokenKind.END, TokenKind.ELSE])
                    else_code = None
                    if self.lexer.next().kind == TokenKind.ELSE:
                        else_code = self.parse_statements_until()
                        _ = self.lexer.next()
                    if token.kind == TokenKind.IF:
                        node: NodeIf = {"lhs": lhs, "rhs": rhs, "comparison": comparison, "body": body, "kind":NodeKind.IF, "else":else_code}
                        result.append(node)
                    else:
                        node: NodeWhile = {"lhs": lhs, "rhs": rhs, "comparison": comparison, "body": body, "kind":NodeKind.WHILE}
                        result.append(node)
                case TokenKind.RETURN:
                    node: NodeReturn = {"body": self.parse_expr_until(), "kind":NodeKind.RETURN}
                    result.append(node)
                case TokenKind.IDENTIFIER:
                    match self.lexer.peek_next_token().kind:
                        case TokenKind.COLON:
                            _ = self.lexer.next()
                            type_ = self.parse_type()
                            node:NodeDecl = {"kind": NodeKind.DECL, "type_":type_, "id":token.value}
                            result.append(node)
                            if self.lexer.peek_next_token().kind == TokenKind.SINGLE_EQUAL:
                                _ = self.lexer.next()
                                body = self.parse_expr_until()
                                node:NodeAssignment = {"kind": NodeKind.ASSIGN, "id":token.value, "body":body}
                                result.append(node)
                        case TokenKind.SINGLE_EQUAL:
                            _ = self.lexer.next()
                            body = self.parse_expr_until()
                            node:NodeAssignment = {"kind": NodeKind.ASSIGN, "body": body, "id":token.value}
                            result.append(node)
                        case TokenKind.LPAREN:
                            body = self.parse_expr_until(startwith=token)
                            node:NodeExpr = {"kind": NodeKind.EXPR, "body": body}
                            result.append(node)
                        case _:
                            eprint(f"Expected : or = after identifier {token}")
        return result
    
    #parses an expression until a desired token is reached 
    def parse_expr_until(self, until: list[TokenKind]=[TokenKind.NEWLINE, TokenKind.SEMICOLON], startwith:Optional[Token]=None) -> ExprFull:
        result: ExprFull = []
        while self.lexer.peek_next_token().kind not in until:
            token = None
            if startwith:
                token = startwith
            else:
                token = self.lexer.next()
            if token.kind not in Parser.expression_tokens:
                eprint(f"Unexpected Token In Expression {token}")
            match token.kind:
                case TokenKind.LITERAL_INT:
                    result.append(NameTypePair(token.value, "int"))
                case TokenKind.LITERAL_FLOAT:
                    result.append(NameTypePair(token.value, "float"))
                case TokenKind.LITERAL_STRING:
                    result.append(NameTypePair(token.value, "string"))
                case TokenKind.LITERAL_BOOL:
                    result.append(NameTypePair(token.value, "bool"))
                case TokenKind.IDENTIFIER:
                    if self.lexer.peek_next_token().kind == TokenKind.LPAREN:
                        _ = self.lexer.next()
                        name = token.value
                        args = []
                        while True:
                            args.append(self.parse_expr_until([TokenKind.COMMA, TokenKind.RPAREN]))
                            if self.lexer.peek_next_token().kind == TokenKind.RPAREN: break
                            _ = self.lexer.next()
                        _ = self.lexer.next()
                        result.append(FunctionCall(name, args))
                    else:        
                        result.append(token.value)
                case _:
                    result.append(token.value)
        return result
                

    #returns procedure parameters for use in extern/proc defintions (not func call arguments)
    def parse_proc_params(self) -> FuncParams:
        params: FuncParams = []
        self.expect(TokenKind.LPAREN)
        while True:
            if self.lexer.peek_next_token().kind == TokenKind.RPAREN: break
            params.append(NameTypePair(self.lexer.next().value, self.parse_type()))
            if self.lexer.peek_next_token().kind == TokenKind.RPAREN: break
            self.expect(TokenKind.COMMA)
        _ = self.lexer.next()
        return params
    
    #if the parser expects a type to be next this will parse the type and return it as a string
    def parse_type(self) -> str:
        initial = self.lexer.next()
        match initial.kind:
            case TokenKind.IDENTIFIER:
                return initial.value
            case TokenKind.HAT:
                rest = self.expect(TokenKind.IDENTIFIER, False).value
                return initial.value+rest
            case _:
                eprint(f"Unexpected Token {initial} Expected Type.")

    #checks if the next token matches what is expected if consume is true does not return the token
    def expect(self, expect: TokenKind, consume:bool = True) -> Optional[Token]:
        if self.lexer.peek_next_token().kind != expect:
            eprint(f"Unexpected Token {self.lexer.next()} Expected {expect.name.lower()}")
        if consume: _ = self.lexer.next()
        else: return self.lexer.next()