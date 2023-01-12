from typing import TypedDict, NamedTuple, Union, Optional

from lexer import *
from util import eprint

NameTypePair = NamedTuple("NameTypePair", name=str, type_=str)
FunctionCall = NamedTuple("FunctionCall", name=str, args=list["ExprFull"])

#a value literal would contain a type so strings can be decerned from identifiers.
ExprNode = Union[NameTypePair, str, FunctionCall]
ExprFull = list[ExprNode]
Statement = Union["NodeIf", "NodeReturn", "NodeWhile", "NodeDecl", "NodeAssignment"]

FuncParams =  list[NameTypePair]

NodeExtern = TypedDict('NodeExtern', {'name': str, 'params': FuncParams, 'type_': str,})
NodeFunc = TypedDict('NodeFunc', {'name': str, 'params': FuncParams, 'type_': str, "body": list[Statement], "pub": bool})
NodeIf = TypedDict("NodeIf", {"lhs": ExprFull, "rhs": ExprFull, "comparison": str, "body": list[Statement]})
NodeWhile = TypedDict("NodeWhile", {"lhs": ExprFull, "rhs": ExprFull, "comparison": str, "body": list[Statement]})
NodeDecl = TypedDict("NodeDecl", {"id": str, "type_": str, "body": Optional[ExprFull]})
NodeAssignment = TypedDict("NodeDecl", {"id": str, "body": ExprFull})
NodeReturn = TypedDict("NodeReturn", {"body": ExprFull})
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
                    node:NodeExtern = {"name": name, "params": params, "type_": return_type}
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
                    node:NodeFunc = {"name": name, "params": params, "type_": return_type, "pub": self.next_proc_pub, "body":body}
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
        while self.lexer.peek_next_token().kind not in until:
            token = self.lexer.next()
            result: list[Statement]
            match token.kind:
    
    #parses an expression until a desired token is reached 
    def parse_expr_until(self, until: list[Tokenkind]=[TokenKind.NEWLINE, TokenKind.SEMICOLON]) -> ExprFull:
        pass
                

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

    #checks if the next token matches what is expected if consume is true does not return the token
    def expect(self, expect: TokenKind, consume:bool = True) -> Optional[Token]:
        if self.lexer.peek_next_token().kind != expect:
            eprint(f"Unexpected Token {self.lexer.next()} Expected {expect.name.lower()}")
        if consume: _ = self.lexer.next()
        else: return self.lexer.next()