from typing import TypedDict, NamedTuple, Union, Optional

from lexer import *
from util import eprint

NameTypePair = NamedTuple("NameTypePair", name=str, id=int)
FunctionCall = NamedTuple("FunctionCall", name=str, args=list["ExprFull"])

#a value literal would contain a type a string would be an identfier or + - ...
ExprNode = Union[NameTypePair, str, FunctionCall]
ExprFull = list[ExprNode]
Statement = Union["NodeIf", "NodeReturn", "NodeWhile", "NodeDecl", "NodeAssignment"]

FuncParams = NamedTuple("FuncParams", list[NameTypePair])

NodeExtern = TypedDict('NodeExtern', {'name': str, 'params': FuncParams, 'type_': str,})
NodeFunc = TypedDict('NodeFunc', {'name': str, 'params': FuncParams, 'type_': str, "body": list[Statement]})
NodeIf = TypedDict("NodeIf", {"lhs": ExprFull, "rhs": ExprFull, "comparison": str, "body": list[Statement]})
NodeWhile = TypedDict("NodeWhile", {"lhs": ExprFull, "rhs": ExprFull, "comparison": str, "body": list[Statement]})
NodeDecl = TypedDict("NodeDecl", {"id": str, "type_": str, "body": Optional[ExprFull]})
NodeAssignment = TypedDict("NodeDecl", {"id": str, "body": ExprFull})
NodeReturn = TypedDict("NodeReturn", {"body": ExprFull})



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
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
    
    #returns a pseudo ast representing the program consumes the until token
    def parse_until(self, until:list[TokenKind]=[TokenKind.EOF]):
        result = {}
        while True:
            token = self.lexer.peek_next_token()
            if token.kind in until:
                break
            token = self.lexer.next()
            match token.kind:
                case TokenKind.EXTERN: result[token.value] = self.parse_function_signature(TokenKind.NEWLINE)
                case TokenKind.PROC:
                    func = self.parse_function_signature()
                    func["body"] = self.parse_until([TokenKind.END])
                    _ = self.lexer.next()
                    result[token.value] = func
                case TokenKind.IF | TokenKind.WHILE:
                    statement = {}
                    statement["lhs"] = self.get_values_until(Parser.comparison_tokens)
                    statement["comparison"] = self.lexer.next().kind.name.lower()
                    statement["rhs"] = self.get_values_until([TokenKind.DO])
                    statement["body"] = self.parse_until([TokenKind.END, TokenKind.ELSE])
                    statement["else"] = None
                    if self.lexer.peek_next_token().kind == TokenKind.ELSE:
                        _ = self.lexer.next()
                        statement["else"] = self.parse_until([TokenKind.END])
                    _ = self.lexer.next()
                    result[token.value] = statement
                case TokenKind.RETURN:
                    result[token.value] = {"expr": self.get_values_until()}
                case TokenKind.IDENTIFIER:
                    statement = {}
                    next_ = self.lexer.next()
                    if next_.kind == TokenKind.COLON:
                        statement["is_decl"] = True
                        statement["type"] = self.parse_type()
                        if self.lexer.peek_next_token().kind == TokenKind.SINGLE_EQUAL:
                            _ = self.lexer.next()
                            statement["expr"] = self.get_values_until()
                    elif next_.kind == TokenKind.SINGLE_EQUAL:
                        statement["is_decl"] = False
                        statement["expr"] = self.get_values_until()
                    else:
                        print(f"Unexpected Token After Identifier {next_}")
                    result[token.value] = statement
                
                case _:
                    pass
        return result        


    #returns all tokens between brackets (not recursive)
    #the type of bracket can be passed in as a parameter
    #has the same type as the parse function a funky list of tokens
    #consumes the last brakcet
    def parse_brackets(self, bracket:TokenKind=TokenKind.RPAREN):
        result = []
        while True:
            result.append(self.get_values_until([TokenKind.COMMA, bracket]))
            if self.lexer.next().kind == bracket:
                return result
    
    #get token values until an a certain type does not consume the last one
    def get_values_until(self, until: list[TokenKind]=[TokenKind.NEWLINE]) -> list[dict[str, TokenKind]]:
        tk = self.lexer.peek_next_token()
        result = []
        while tk.kind not in until:
            tk = self.lexer.next()
            result.append((tk.value, tk.kind))
            tk = self.lexer.peek_next_token()
        return result
    
    #parse an expected type
    def parse_type(self) -> Optional[str]:
        start_tk = self.lexer.peek_next_token()
        match start_tk.kind:
            case TokenKind.IDENTIFIER:
                _ = self.lexer.next()
                return start_tk.value
            case TokenKind.HAT:
                _ = self.lexer.next()
                name = self.expect(TokenKind.IDENTIFIER).value
                return start_tk.value + name
            case _:
                return None
    
    #parse a type from a list of tokens
    def parse_type_from(self, tokens: list[Token]) -> str:
        start_tk = tokens[0]
        match start_tk.kind:
            case TokenKind.IDENTIFIER:
                return start_tk.value
            case TokenKind.HAT:
                name = tokens[1]
                return start_tk.value + name.value
            case _:
                return None

    #returns an object with the properties for a signature set
    def parse_function_signature(self, expected_after_end: TokenKind = TokenKind.DO):
        result = {}
        
        #function name
        result["name"] = self.lexer.next().value

        _ = self.expect(TokenKind.LPAREN)

        #add our parameters (if any)
        params = self.parse_brackets()
        result["params"] = {}
        for p in params:
            type_ = ""
            for v in p[1:]:
                type_ += v[0]
            if len(p) > 0:
                result["params"][p[0][0]] = type_

        #add the return type
        result["return_type"] = None
        if self.lexer.peek_next_token().kind != expected_after_end:
            result["return_type"] = self.parse_type()

        return result
    
    #makes sure the next token is of a certain type returns that token back to the caller if so
    def expect(self, kind:TokenKind) -> Token:
        if self.lexer.peek_next_token().kind != kind:
            eprint(f"Unexpected Token {self.lexer.next()} expected {kind.name}")
        return self.lexer.next()
        